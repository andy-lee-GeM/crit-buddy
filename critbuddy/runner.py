#!/usr/bin/env python3
"""
Criticality study runner.

Usage:
    python run_study.py <experiment.yaml>
    python run_study.py <experiment.yaml> --solver openmc
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from critbuddy.core.config import ExperimentConfig, generate_cases
from critbuddy.core.template_loader import load_template_class
from critbuddy.reporting import generate_report, plot_heatmap, plot_keff
from critbuddy.solvers import OpenMCSolver, MCNPSolver
from critbuddy.utils import Status, setup_logging, get_logger

logger = get_logger(__name__)


def load_config() -> dict:
    """Load config.yaml and set process-level environment variables."""
    config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        return {}

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    if "openmc_cross_sections" in config and not os.getenv("OPENMC_CROSS_SECTIONS"):
        xs_path = config["openmc_cross_sections"]
        if Path(xs_path).exists():
            os.environ["OPENMC_CROSS_SECTIONS"] = xs_path

    if "mcnp" in config and "executable" in config["mcnp"] and not os.getenv("MCNP_EXECUTABLE"):
        mcnp_path = config["mcnp"]["executable"]
        if Path(mcnp_path).exists():
            os.environ["MCNP_EXECUTABLE"] = mcnp_path

    return config


def create_run_directory(experiment_dir: Path, run_name: str) -> Path:
    """Create a timestamped run directory under experiment_dir/runs/{run_name}/."""
    runs_dir = experiment_dir / "runs" / run_name
    runs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = runs_dir / timestamp
    run_dir.mkdir(parents=True)
    (run_dir / "cases").mkdir()

    latest_link = runs_dir / "latest"
    if latest_link.is_symlink():
        latest_link.unlink()
    elif latest_link.exists():
        if latest_link.is_dir():
            shutil.rmtree(latest_link)
        else:
            latest_link.unlink()
    latest_link.symlink_to(timestamp, target_is_directory=True)

    return run_dir


def create_solvers(solver_name: str = "openmc") -> list:
    """Create solver instances for openmc, mcnp, or all."""
    solvers = []

    if solver_name in ("openmc", "all"):
        solvers.append(OpenMCSolver())

    if solver_name in ("mcnp", "all"):
        mcnp_solver = MCNPSolver()
        if mcnp_solver.is_available():
            solvers.append(mcnp_solver)
        else:
            print("  Warning: MCNP not available, skipping")

    return solvers


@dataclass
class RunContext:
    """Inputs and resolved paths for a single config run."""

    config_path: Path
    experiment_dir: Path
    config: ExperimentConfig
    template: object
    template_dir: Path
    cases: list
    solvers: list
    run_name: str
    run_dir: Path


def _resolve_experiment_dir(config_path: Path) -> Path:
    parent = config_path.parent
    return parent.parent if parent.name == "_config" else parent


def _prepare_run_context(config_path: Path, solver: str, run_name: str | None) -> RunContext:
    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    experiment_dir = _resolve_experiment_dir(config_path)
    config = ExperimentConfig.from_file(config_path)
    template = load_template_class(config.problem)
    template_dir = Path(__file__).parent.parent / "templates" / config.problem

    cases = generate_cases(config, template)
    if not cases:
        raise RuntimeError("No cases generated from config")

    solvers = create_solvers(solver)
    if not solvers:
        raise RuntimeError("No solvers available")

    resolved_run_name = run_name if run_name else config_path.stem
    run_dir = create_run_directory(experiment_dir, resolved_run_name)
    shutil.copy(config_path, run_dir / "config.yaml")

    return RunContext(
        config_path=config_path,
        experiment_dir=experiment_dir,
        config=config,
        template=template,
        template_dir=template_dir,
        cases=cases,
        solvers=solvers,
        run_name=resolved_run_name,
        run_dir=run_dir,
    )


def _print_run_header(context: RunContext) -> None:
    print(
        f"""
{'=' * 80}
                    CRITICALITY STUDY RUNNER
{'=' * 80}
Experiment: {context.config.name}
Problem:    {context.config.problem}
Path:       {context.experiment_dir}
{'=' * 80}
"""
    )
    print(f"Solvers: {', '.join(s.name.upper() for s in context.solvers)}")
    print(f"Cases: {len(context.cases)}")
    print(f"Run directory: {context.run_dir}")


def _run_solver_cases(context: RunContext) -> dict[str, list[dict]]:
    all_results: dict[str, list[dict]] = {}

    for solver_backend in context.solvers:
        all_results[solver_backend.name] = run_cases(
            solver_backend,
            context.cases,
            context.run_dir,
            context.template_dir,
            context.template.SAFETY_LIMIT,
        )

    return all_results


def _generate_outputs(context: RunContext, results_csv: Path) -> None:
    plot_paths = plot_keff(
        results_csv,
        output_dir=context.run_dir / "plots",
        safety_limit=context.template.SAFETY_LIMIT,
    )
    heatmap_paths = plot_heatmap(
        results_csv,
        output_dir=context.run_dir / "plots",
        safety_limit=context.template.SAFETY_LIMIT,
    )
    plot_paths.extend(heatmap_paths)

    if plot_paths:
        print(f"\nPlots: {context.run_dir / 'plots'}")

    try:
        report_path = generate_report(context.run_dir, context.config_path)
        print(f"Report: {report_path}")
    except Exception as exc:
        print(f"Warning: Could not generate report: {exc}")


def run_cases(solver_backend, cases, run_dir: Path, template_dir: Path, safety_limit: float) -> list[dict]:
    """Run all cases with one solver backend (sequential only)."""
    results: list[dict] = []
    total_cases = len(cases)

    print(f"\n  Running {solver_backend.name.upper()} solver...")

    for idx, case in enumerate(cases, start=1):
        params = {**case.all_params, "CASE_LABEL": case.label}
        case_name = case.label.replace(" ", "_").replace("-", "")
        case_dir = run_dir / "cases" / case_name / solver_backend.name
        case_dir.mkdir(parents=True, exist_ok=True)

        print(f"  [{idx}/{total_cases}] {case.label}")

        result = solver_backend.run(
            params=params,
            case_label=case.label,
            case_dir=case_dir,
            template_dir=template_dir,
            safety_limit=safety_limit,
        )

        if result.status in (Status.FAILED, Status.SKIPPED):
            msg = result.errors[0] if result.errors else ""
            print(f"    Result: [{result.status.value}] {msg}")
        else:
            print(f"    Result: k-eff = {result.keff:.5f} +/- {result.uncertainty:.5f} [{result.status.value}]")

        results.append(
            {
                "case": case.label,
                "solver": solver_backend.name,
                "keff": result.keff,
                "std": result.uncertainty,
                "k2s": result.k2sigma,
                "status": result.status,
                "execution_time": result.execution_time,
                "user_params": case.user_params,
            }
        )

    return results


def write_results(run_dir: Path, all_results: dict[str, list[dict]]) -> Path | None:
    """Write results.csv with a union of all user parameter columns."""
    results_path = run_dir / "results.csv"

    rows = [
        row
        for solver_rows in all_results.values()
        for row in solver_rows
        if row["status"] not in (Status.FAILED, Status.SKIPPED)
    ]

    if not rows:
        print("\nNo successful results to write")
        return None

    param_names = sorted(
        {
            key
            for row in rows
            for key in row.get("user_params", {}).keys()
        }
    )

    header = ["case", "solver", "keff", "std", "keff_2sigma", "status", "execution_time", *param_names]

    with open(results_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for row in rows:
            status_str = row["status"].value if isinstance(row["status"], Status) else row["status"]
            base_values = [
                row["case"],
                row["solver"],
                f"{row['keff']:.5f}",
                f"{row['std']:.5f}",
                f"{row['k2s']:.5f}",
                status_str,
                f"{row['execution_time']:.1f}",
            ]
            param_values = [row.get("user_params", {}).get(param, "") for param in param_names]
            writer.writerow(base_values + param_values)

    print(f"\nResults written to: {results_path}")
    return results_path


def print_summary(all_results: dict[str, list[dict]]) -> None:
    """Print result table for all solvers and cases."""
    print(f"\n{'=' * 80}")
    print(f"{'Case':<20} {'Solver':<8} {'k-eff':>10} {'std':>10} {'k+2s':>10} {'Status':>10}")
    print("-" * 80)

    for solver_rows in all_results.values():
        for row in solver_rows:
            status_str = row["status"].value if isinstance(row["status"], Status) else row["status"]
            if row["status"] in (Status.FAILED, Status.SKIPPED):
                print(f"{row['case']:<20} {row['solver']:<8} {'---':>10} {'---':>10} {'---':>10} {status_str:>10}")
            else:
                print(
                    f"{row['case']:<20} {row['solver']:<8} "
                    f"{row['keff']:>10.5f} {row['std']:>10.5f} {row['k2s']:>10.5f} {status_str:>10}"
                )

    print("=" * 80)


def run_analysis(
    config_path: Path,
    solver: str = "openmc",
    run_name: str | None = None,
    generate_outputs: bool = True,
) -> Path:
    """Run one experiment config end-to-end."""
    context = _prepare_run_context(config_path, solver=solver, run_name=run_name)
    _print_run_header(context)

    all_results = _run_solver_cases(context)
    results_csv = write_results(context.run_dir, all_results)
    print_summary(all_results)

    if generate_outputs and results_csv and results_csv.exists():
        _generate_outputs(context, results_csv)

    print(f"\nResults: {context.run_dir}")
    print(f"Latest:  {context.experiment_dir / 'runs' / context.run_name / 'latest'}")
    return context.run_dir


def main() -> None:
    load_config()

    parser = argparse.ArgumentParser(description="Run criticality analysis")
    parser.add_argument("experiment", help="Path to experiment YAML")
    parser.add_argument("--solver", choices=["openmc", "mcnp", "all"], default="openmc")
    parser.add_argument("--name", help="Custom run name (default: YAML filename)")
    parser.add_argument("--no-report", action="store_true", help="Skip plot/report generation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (warnings only)")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose, quiet=args.quiet)

    try:
        run_analysis(
            config_path=Path(args.experiment),
            solver=args.solver,
            run_name=args.name,
            generate_outputs=not args.no_report,
        )
    except Exception as exc:
        logger.exception("Analysis failed")
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
