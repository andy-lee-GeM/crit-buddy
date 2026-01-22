#!/usr/bin/env python3
"""
Criticality Study Runner.

Usage:
    python run_study.py <experiment.yaml>
    python run_study.py <experiment.yaml> --validate
    python run_study.py <experiment.yaml> --smoke
    python run_study.py <experiment.yaml> --solver openmc
"""

import argparse
import csv
import importlib.util
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

from critbuddy.core.config import ExperimentConfig, generate_cases
from critbuddy.solvers import OpenMCSolver, MCNPSolver
from critbuddy.utils import Status, working_directory, setup_logging, get_logger
from critbuddy.reporting import print_report, save_report


def load_config():
    """Load configuration from config.yaml and set environment variables."""
    config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        return {}

    with open(config_path) as f:
        config = yaml.safe_load(f) or {}

    if "openmc_cross_sections" in config:
        if not os.getenv("OPENMC_CROSS_SECTIONS"):
            xs_path = config["openmc_cross_sections"]
            if Path(xs_path).exists():
                os.environ["OPENMC_CROSS_SECTIONS"] = xs_path

    if "mcnp" in config and "executable" in config["mcnp"]:
        if not os.getenv("MCNP_EXECUTABLE"):
            mcnp_path = config["mcnp"]["executable"]
            if Path(mcnp_path).exists():
                os.environ["MCNP_EXECUTABLE"] = mcnp_path

    return config


def load_template_class(template_name: str):
    """Load template class by name from templates directory."""
    templates_dir = Path(__file__).parent.parent / "templates"
    template_init = templates_dir / template_name / "__init__.py"

    if not template_init.exists():
        raise ValueError(f"Template '{template_name}' not found at {template_init}")

    spec = importlib.util.spec_from_file_location(
        f"templates.{template_name}",
        template_init
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "Template"):
        raise ValueError(f"Template '{template_name}' must export a 'Template' class")

    return module.Template()


def load_template_module(template_dir: Path):
    """Load template's model.py module."""
    template_path = template_dir / "openmc" / "model.py"
    if not template_path.exists():
        template_path = template_dir / "model.py"
    spec = importlib.util.spec_from_file_location("model", template_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_run_directory(experiment_dir: Path) -> Path:
    """Create timestamped run directory."""
    runs_dir = experiment_dir / "runs"
    runs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = runs_dir / timestamp
    run_dir.mkdir(parents=True)
    (run_dir / "cases").mkdir()

    # Update 'latest' symlink
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


def create_solvers(solver: str = "openmc"):
    """
    Create solver instances.

    Args:
        solver: "openmc", "mcnp", or "all"
    """
    solvers = []

    if solver in ("openmc", "all"):
        solvers.append(OpenMCSolver())

    if solver in ("mcnp", "all"):
        mcnp_solver = MCNPSolver()
        if mcnp_solver.is_available():
            solvers.append(mcnp_solver)
        else:
            print("  Warning: MCNP not available, skipping")

    return solvers


def validate_geometry(template_module, case, experiment_dir, template_dir):
    """Visualize geometry for validation."""
    print("\n" + "=" * 60)
    print("  GEOMETRY VALIDATION")
    print("=" * 60)
    print(f"\nValidating with: {case.label}")

    val_dir = experiment_dir / "_validation"
    val_dir.mkdir(exist_ok=True)

    with working_directory(val_dir):
        import openmc
        materials, geometry, dims = template_module.build_model(case.all_params)
        template_module.print_summary(case.all_params, dims)

        materials.export_to_xml()
        geometry.export_to_xml()

        plots, _ = template_module.create_plots(dims, materials)
        plots.export_to_xml()
        openmc.plot_geometry()

        for i, name in enumerate(["xy", "xz"], 1):
            src = Path(f"plot_{i}.png")
            if src.exists():
                src.rename(f"{name}.png")

    print(f"\nGeometry plots: {val_dir}/xy.png, {val_dir}/xz.png")


def run_cases(solver, cases, run_dir, template_dir, safety_limit):
    """Run all cases with a solver."""
    results = []
    original_dir = Path.cwd()

    print(f"\n  Running {solver.name.upper()} solver...")

    for case in cases:
        params = {**case.all_params, "CASE_LABEL": case.label}
        case_name = case.label.replace(" ", "_").replace("-", "")
        case_dir = run_dir / "cases" / case_name / solver.name
        case_dir.mkdir(parents=True, exist_ok=True)

        print(f"    {case.label:<20}", end="", flush=True)

        result = solver.run(
            params=params,
            case_label=case.label,
            case_dir=case_dir,
            template_dir=template_dir,
            safety_limit=safety_limit,
        )
        os.chdir(original_dir)

        if result.status in (Status.FAILED, Status.SKIPPED):
            print(f"  [{result.status.value}] {result.errors[0] if result.errors else ''}")
        else:
            print(f"  k-eff = {result.keff:.5f} +/- {result.uncertainty:.5f}  [{result.status.value}]")

        results.append({
            "case": case.label,
            "solver": solver.name,
            "keff": result.keff,
            "std": result.uncertainty,
            "k2s": result.k2sigma,
            "status": result.status,
            "execution_time": result.execution_time,
            "user_params": case.user_params,  # Store for CSV output
        })

    return results


def write_results(run_dir, all_results):
    """Write results.csv with parameter columns."""
    results_path = run_dir / "results.csv"
    rows = [r for results in all_results.values() for r in results if r["status"] not in (Status.FAILED, Status.SKIPPED)]

    if not rows:
        print("\nNo successful results to write")
        return

    # Get all parameter names from first result
    param_names = sorted(rows[0].get("user_params", {}).keys())

    # Build header
    base_cols = ["case", "solver", "keff", "std", "keff_2sigma", "status", "execution_time"]
    header = base_cols + param_names

    with open(results_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for r in rows:
            status_str = r["status"].value if isinstance(r["status"], Status) else r["status"]
            base_values = [
                r["case"],
                r["solver"],
                f"{r['keff']:.5f}",
                f"{r['std']:.5f}",
                f"{r['k2s']:.5f}",
                status_str,
                f"{r['execution_time']:.1f}",
            ]
            param_values = [r.get("user_params", {}).get(p, "") for p in param_names]
            writer.writerow(base_values + param_values)

    print(f"\nResults written to: {results_path}")


def print_summary(all_results):
    """Print results summary table."""
    print(f"\n{'=' * 80}")
    print(f"{'Case':<20} {'Solver':<8} {'k-eff':>10} {'std':>10} {'k+2s':>10} {'Status':>10}")
    print("-" * 80)

    for results in all_results.values():
        for r in results:
            status_str = r["status"].value if isinstance(r["status"], Status) else r["status"]
            if r["status"] not in (Status.FAILED, Status.SKIPPED):
                print(f"{r['case']:<20} {r['solver']:<8} {r['keff']:>10.5f} {r['std']:>10.5f} {r['k2s']:>10.5f} {status_str:>10}")
            else:
                print(f"{r['case']:<20} {r['solver']:<8} {'---':>10} {'---':>10} {'---':>10} {status_str:>10}")
    print("=" * 80)


def run_experiment(experiment_path: Path, args):
    """Run an experiment."""
    experiment_path = experiment_path.resolve()
    experiment_dir = experiment_path.parent

    # Load config
    config = ExperimentConfig.from_file(experiment_path)

    # Load template
    template_class = load_template_class(config.problem)
    template_dir = Path(__file__).parent.parent / "templates" / config.problem
    template_module = load_template_module(template_dir)

    print(f"""
================================================================================
                    CRITICALITY STUDY RUNNER
================================================================================
Experiment: {config.name}
Problem:    {config.problem}
Path:       {experiment_dir}
================================================================================
""")

    # Generate cases
    cases = generate_cases(config, template_class, smoke_test=args.smoke)

    if args.smoke:
        print("SMOKE TEST MODE: 1 case, minimal particles")

    # Validation mode
    if args.validate:
        validate_geometry(template_module, cases[0], experiment_dir, template_dir)
        return

    # Setup solvers (default: OpenMC only, use --solver flag to change)
    solvers = create_solvers(args.solver or "openmc")

    if not solvers:
        print("Error: No solvers available")
        sys.exit(1)

    print(f"Solvers: {', '.join(s.name.upper() for s in solvers)}")

    # Filter cases
    if args.case:
        cases = [c for c in cases if c.label == args.case]
        if not cases:
            print(f"Error: Case '{args.case}' not found")
            sys.exit(1)

    print(f"Cases: {len(cases)}")

    # Create run directory
    run_dir = create_run_directory(experiment_dir)
    shutil.copy(experiment_path, run_dir / "config.yaml")
    print(f"Run directory: {run_dir}")

    # Run solvers
    original_dir = Path.cwd()
    all_results = {}

    for solver in solvers:
        results = run_cases(solver, cases, run_dir, template_dir, template_class.SAFETY_LIMIT)
        all_results[solver.name] = results
        os.chdir(original_dir)

    # Output
    write_results(run_dir, all_results)
    print_summary(all_results)

    # Generate report if requested
    if args.report:
        results_csv = run_dir / "results.csv"
        if results_csv.exists():
            print("\nGenerating report...")
            report_path = save_report(
                results_csv,
                output_dir=run_dir,
                safety_limit=template_class.SAFETY_LIMIT,
            )
            print(f"Report: {report_path}")

    print(f"\nResults: {run_dir}")
    print(f"Latest:  {experiment_dir / 'runs' / 'latest'}")


def main():
    load_config()

    parser = argparse.ArgumentParser(description="Run criticality experiment")
    parser.add_argument("experiment", nargs="?", help="Path to experiment.yaml")
    parser.add_argument("--validate", action="store_true", help="Visualize geometry only")
    parser.add_argument("--case", help="Run specific case label")
    parser.add_argument("--solver", choices=["openmc", "mcnp", "all"], help="Override solver")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke test")
    parser.add_argument("--report", action="store_true", help="Generate report after run")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (warnings only)")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(verbose=args.verbose, quiet=args.quiet)
    logger.debug("Crit-buddy starting")

    if not args.experiment:
        parser.print_help()
        sys.exit(1)

    run_experiment(Path(args.experiment), args)


if __name__ == "__main__":
    main()
