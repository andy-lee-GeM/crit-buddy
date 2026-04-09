#!/usr/bin/env python3
"""
Criticality study runner.

Usage:
    python run_study.py <experiment.yaml>
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

from critbuddy.reporting import plot_keff
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
    """Create solver instances for config-driven runs."""
    from critbuddy.solvers import OpenMCSolver

    if solver_name != "openmc":
        raise ValueError("Config-driven runs only support the OpenMC solver")

    return [OpenMCSolver()]


@dataclass
class RunContext:
    """Inputs and resolved paths for a single config run."""

    config_path: Path
    experiment_dir: Path
    config: ExperimentConfig
    definition: object
    definition_dir: Path
    cases: list
    solvers: list
    run_name: str
    run_dir: Path


def _resolve_experiment_dir(config_path: Path) -> Path:
    parent = config_path.parent
    return parent.parent if parent.name in {"_config", "configs"} else parent


def _resolve_definition(config: ExperimentConfig) -> tuple[object, Path]:
    from critbuddy.core.template_loader import load_model_class, load_template_class

    root = Path(__file__).parent.parent
    if config.model:
        definition_dir = root / "models" / config.model
        return load_model_class(config.model), definition_dir

    if config.problem:
        definition_dir = root / "templates" / config.problem
        return load_template_class(config.problem), definition_dir

    raise RuntimeError("Config did not resolve to a model or problem definition")


def _prepare_run_context(config_path: Path, solver: str, run_name: str | None) -> RunContext:
    from critbuddy.core.config import ExperimentConfig, generate_cases

    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    experiment_dir = _resolve_experiment_dir(config_path)
    config = ExperimentConfig.from_file(config_path)
    definition, definition_dir = _resolve_definition(config)

    cases = generate_cases(config, definition)
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
        definition=definition,
        definition_dir=definition_dir,
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
Type:       {context.config.definition_kind}
Definition: {context.config.definition_name}
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
            context.definition_dir,
            context.definition.SAFETY_LIMIT,
        )

    return all_results


def _generate_outputs(context: RunContext, results_csv: Path) -> None:
    plot_paths = plot_keff(
        results_csv,
        output_dir=context.run_dir / "plots",
        safety_limit=context.definition.SAFETY_LIMIT,
    )

    if plot_paths:
        print(f"\nPlots: {context.run_dir / 'plots'}")


def _build_display_params(user_params: dict, derived_params: dict) -> dict:
    """
    Build user-facing result parameters with derived values overlaid when they
    resolve an existing user key.

    Example:
    - user config provides `fill_fraction_percent`
    - template derives the effective `FILL_HEIGHT_CM`
    - results.csv should show the resolved `fill_height_cm`, not the default
    """
    display_params = dict(user_params)

    for derived_key, derived_value in derived_params.items():
        user_key = derived_key.lower()
        if user_key in display_params:
            display_params[user_key] = derived_value

    # Preserve key derived companion parameters in results.csv when the user
    # supplied a paper-facing or library-facing moderation input.
    if "h_over_x" in display_params and "H_TO_U" in derived_params:
        display_params["h_to_u"] = derived_params["H_TO_U"]
    if "h_to_u" in display_params and "H_OVER_X" in derived_params:
        display_params["h_over_x"] = derived_params["H_OVER_X"]
    if (
        ("h_over_x" in display_params or "h_to_u" in display_params)
        and "UO2F2_DENSITY_G_CM3" in derived_params
    ):
        display_params["uo2f2_density_g_cm3"] = derived_params["UO2F2_DENSITY_G_CM3"]

    return display_params


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
                "display_params": _build_display_params(case.user_params, case.derived_params),
            }
        )

    return results


def validate_geometry(
    config_path: Path,
    solver: str = "openmc",
) -> Path:
    """Generate a geometry validation image for the first case in a config."""
    from critbuddy.core.config import ExperimentConfig, generate_cases

    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    experiment_dir = _resolve_experiment_dir(config_path)
    config = ExperimentConfig.from_file(config_path)
    definition, definition_dir = _resolve_definition(config)

    cases = generate_cases(config, definition)
    if not cases:
        raise RuntimeError("No cases generated from config")

    solvers = create_solvers(solver)
    if not solvers:
        raise RuntimeError("No solvers available")

    validation_dir = experiment_dir / "_validation"
    first_case = cases[0]

    for solver_backend in solvers:
        image_path = solver_backend.validate(
            params=first_case.all_params,
            case_dir=validation_dir,
            template_dir=definition_dir,
        )
        if image_path:
            print(f"Validated case: {first_case.label}")
            print(f"Geometry:      {image_path}")
            return image_path

    raise RuntimeError("Selected solver does not support geometry validation")


def write_results(run_dir: Path, all_results: dict[str, list[dict]]) -> Path | None:
    """Write results.csv with a union of all display parameter columns."""
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
            for key in row.get("display_params", row.get("user_params", {})).keys()
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
            display_params = row.get("display_params", row.get("user_params", {}))
            param_values = [display_params.get(param, "") for param in param_names]
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
    parser.add_argument("experiment", help="Path to a study/request/model YAML config")
    parser.add_argument("--solver", choices=["openmc"], default="openmc")
    parser.add_argument("--name", help="Custom run name (default: YAML filename)")
    parser.add_argument("--validate", action="store_true", help="Generate geometry validation output only")
    parser.add_argument("--no-report", action="store_true", help="Skip plot/report generation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (warnings only)")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose, quiet=args.quiet)

    try:
        if args.validate:
            validate_geometry(
                config_path=Path(args.experiment),
                solver=args.solver,
            )
        else:
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
