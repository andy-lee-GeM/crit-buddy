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
from critbuddy.reporting import (
    create_geometry_plot,
    plot_keff,
    create_voxel_plot,
    get_plot_spec,
    generate_voxel_data,
    export_vti as export_vti_file,
    view_interactive,
)


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


def create_run_directory(experiment_dir: Path, run_name: str) -> Path:
    """Create timestamped run directory under a named subdirectory.

    Args:
        experiment_dir: Base experiment directory
        run_name: Name for the run (typically YAML filename stem)

    Returns:
        Path to the timestamped run directory

    Directory structure:
        experiment_dir/runs/{run_name}/{timestamp}/
        experiment_dir/runs/{run_name}/latest -> {timestamp}
    """
    runs_dir = experiment_dir / "runs" / run_name
    runs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = runs_dir / timestamp
    run_dir.mkdir(parents=True)
    (run_dir / "cases").mkdir()

    # Update 'latest' symlink within the run_name directory
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
        openmc.reset_auto_ids()

        materials, geometry, dims = template_module.build_model(case.all_params)
        template_module.print_summary(case.all_params, dims)

        materials.export_to_xml()
        geometry.export_to_xml()

        # Generate 2D slice plots
        plots, color_legend = template_module.create_plots(dims, materials)
        plots.export_to_xml()
        openmc.plot_geometry()

        for i, name in enumerate(["xy", "xz"], 1):
            src = Path(f"plot_{i}.png")
            if src.exists():
                src.rename(f"{name}.png")

        # Create combined geometry plot
        xy_plot = val_dir / "xy.png"
        xz_plot = val_dir / "xz.png"
        output_path = val_dir / "geometry.png"

        if xy_plot.exists() and xz_plot.exists():
            create_geometry_plot(
                xy_plot_path=xy_plot,
                xz_plot_path=xz_plot,
                output_path=output_path,
                color_legend=color_legend,
            )
            # Clean up intermediate plot files
            xy_plot.unlink()
            xz_plot.unlink()
            yz_plot = val_dir / "yz.png"
            if yz_plot.exists():
                yz_plot.unlink()
            print(f"\nCombined geometry: {output_path}")
        else:
            print(f"\nGeometry plots: {val_dir}/xy.png, {val_dir}/xz.png")


def generate_voxel(
    template_module,
    template,
    case,
    experiment_dir,
    save_vti: bool = False,
    interactive: bool = False,
):
    """Generate 3D voxel visualization.

    Args:
        template_module: Module with build_model() function
        template: ProblemTemplate instance (for optional get_plot_spec)
        case: Case object with parameters
        experiment_dir: Experiment directory path
        save_vti: Also export .vti file for ParaView
        interactive: Launch interactive PyVista viewer
    """
    print("\n" + "=" * 60)
    print("  3D VOXEL VISUALIZATION")
    print("=" * 60)
    print(f"\nGenerating voxel for: {case.label}")

    val_dir = experiment_dir / "_validation"
    val_dir.mkdir(exist_ok=True)

    with working_directory(val_dir):
        import openmc
        openmc.reset_auto_ids()

        materials, geometry, dims = template_module.build_model(case.all_params)

        # Export geometry for OpenMC voxel generation
        materials.export_to_xml()
        geometry.export_to_xml()

        # Get plot spec (auto-computed from bounding box, or template-provided)
        spec = get_plot_spec(geometry, template, dims)

        print("Generating 3D voxel plot...")
        print(f"  Center: ({spec.center[0]:.1f}, {spec.center[1]:.1f}, {spec.center[2]:.1f})")
        print(f"  Width: ({spec.width[0]:.1f}, {spec.width[1]:.1f}, {spec.width[2]:.1f})")

        # Generate voxel data (shared between all output formats)
        voxel_data = generate_voxel_data(geometry, materials, spec)

        # Always generate PNG
        voxel_path = val_dir / "voxel_3d.png"
        create_voxel_plot(
            geometry=geometry,
            materials=materials,
            output_path=voxel_path,
            spec=spec,
        )
        print(f"\nPNG: {voxel_path}")

        # Export VTI if requested
        if save_vti:
            vti_path = val_dir / "geometry.vti"
            export_vti_file(voxel_data, vti_path)
            print(f"VTI: {vti_path} (open in ParaView)")

        # Launch interactive viewer if requested
        if interactive:
            print("\nLaunching interactive viewer...")
            view_interactive(voxel_data)


def run_cases(solver, cases, run_dir, template_dir, safety_limit):
    """Run all cases with a solver."""
    results = []
    original_dir = Path.cwd()
    total_cases = len(cases)

    print(f"\n  Running {solver.name.upper()} solver...")

    for idx, case in enumerate(cases, 1):
        params = {**case.all_params, "CASE_LABEL": case.label}
        case_name = case.label.replace(" ", "_").replace("-", "")
        case_dir = run_dir / "cases" / case_name / solver.name
        case_dir.mkdir(parents=True, exist_ok=True)

        # Print case header on its own line
        print(f"  [{idx}/{total_cases}] {case.label}")

        result = solver.run(
            params=params,
            case_label=case.label,
            case_dir=case_dir,
            template_dir=template_dir,
            safety_limit=safety_limit,
        )
        os.chdir(original_dir)

        # Print result on new line after progress bar clears
        if result.status in (Status.FAILED, Status.SKIPPED):
            print(f"    Result: [{result.status.value}] {result.errors[0] if result.errors else ''}")
        else:
            print(f"    Result: k-eff = {result.keff:.5f} +/- {result.uncertainty:.5f}  [{result.status.value}]")

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


def create_consultant_package(
    run_dir: Path,
    experiment_dir: Path,
    config: "ExperimentConfig",
) -> Path:
    """
    Create a consultant package with all files needed for independent verification.

    Args:
        run_dir: The timestamped run directory containing results
        experiment_dir: The experiment directory containing specification.md
        config: The experiment configuration

    Returns:
        Path to the consultant_package directory
    """
    from critbuddy.core.materials import write_materials_yaml

    package_dir = run_dir / "consultant_package"
    package_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 60)
    print("  GENERATING CONSULTANT PACKAGE")
    print("=" * 60)

    # 1. Copy specification.md
    spec_src = experiment_dir / "specification.md"
    if spec_src.exists():
        shutil.copy(spec_src, package_dir / "specification.md")
        print(f"  + specification.md")
    else:
        print(f"  - specification.md (not found)")

    # 2. Copy geometry visualization
    validation_dir = experiment_dir / "_validation"
    if validation_dir.exists():
        geometry_src = validation_dir / "geometry.png"
        if geometry_src.exists():
            shutil.copy(geometry_src, package_dir / "geometry.png")
            print(f"  + geometry.png")
        else:
            print(f"  - geometry.png (not found)")
    else:
        print(f"  - geometry.png (_validation not found)")

    # 3. Generate materials.yaml
    enrichment = config.user_params.get("enrichment", 5.0)
    uf6_density = config.user_params.get("uf6_density", 5.09)
    write_materials_yaml(
        package_dir / "materials.yaml",
        enrichment_pct=enrichment,
        uf6_density=uf6_density,
    )
    print(f"  + materials.yaml")

    # 4. Copy results
    results_src = run_dir / "results.csv"
    if results_src.exists():
        shutil.copy(results_src, package_dir / "results.csv")
        print(f"  + results.csv")

    # 5. Copy plots
    plots_src = run_dir / "plots"
    if plots_src.exists():
        plots_dst = package_dir / "plots"
        if plots_dst.exists():
            shutil.rmtree(plots_dst)
        shutil.copytree(plots_src, plots_dst)
        print(f"  + plots/")

    # 6. Copy example input files from first case
    cases_dir = run_dir / "cases"
    if cases_dir.exists():
        inputs_dir = package_dir / "example_inputs"
        inputs_dir.mkdir(exist_ok=True)

        # Find first case directory
        case_dirs = sorted([d for d in cases_dir.iterdir() if d.is_dir()])
        if case_dirs:
            first_case = case_dirs[0]

            # Copy OpenMC inputs
            openmc_dir = first_case / "openmc"
            if openmc_dir.exists():
                openmc_dst = inputs_dir / "openmc"
                openmc_dst.mkdir(exist_ok=True)
                for xml_file in ["geometry.xml", "materials.xml", "settings.xml"]:
                    src = openmc_dir / xml_file
                    if src.exists():
                        shutil.copy(src, openmc_dst / xml_file)
                print(f"  + example_inputs/openmc/")

            # Copy MCNP input
            mcnp_dir = first_case / "mcnp"
            if mcnp_dir.exists():
                mcnp_dst = inputs_dir / "mcnp"
                mcnp_dst.mkdir(exist_ok=True)
                mcnp_input = mcnp_dir / "input"
                if mcnp_input.exists():
                    shutil.copy(mcnp_input, mcnp_dst / "input")
                    print(f"  + example_inputs/mcnp/")

    # 7. Create README
    readme_content = f"""# Consultant Verification Package

## Experiment: {config.name}

This package contains all information needed to independently verify
the criticality calculations performed for this experiment.

## Contents

| File | Description |
|------|-------------|
| specification.md | Complete methodology, assumptions, and parameters |
| materials.yaml | Exact isotopic compositions used in calculations |
| results.csv | Calculated k-eff values for all cases |
| geometry.png | Geometry visualization |
| example_inputs/ | Example input files (OpenMC/MCNP) |

## Verification Steps

1. Review specification.md to understand the analysis
2. Build your model using the geometry and materials specified
3. Verify materials.yaml matches your material definitions
4. Run calculations and compare to results.csv
5. Results should match within statistical uncertainty (k-eff ± 2σ)

## Acceptance Criteria

k-eff + 2σ < 0.95 (per ANSI/ANS-8.1)

## Questions

Contact: [Your contact information]
"""
    (package_dir / "README.md").write_text(readme_content)
    print(f"  + README.md")

    print("=" * 60)
    print(f"\nConsultant package: {package_dir}")

    return package_dir


def run_experiment(experiment_path: Path, args):
    """Run an experiment."""
    experiment_path = experiment_path.resolve()

    # Determine experiment root directory
    # If YAML is in _config/, go up one level to the experiment root
    parent = experiment_path.parent
    if parent.name == "_config":
        experiment_dir = parent.parent
    else:
        experiment_dir = parent

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

    # Voxel mode (standalone 3D visualization)
    if args.voxel or args.vti or args.interactive:
        generate_voxel(
            template_module,
            template_class,
            cases[0],
            experiment_dir,
            save_vti=args.vti,
            interactive=args.interactive,
        )
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

    # Determine run name (CLI override or YAML filename)
    run_name = args.name if args.name else experiment_path.stem

    # Create run directory
    run_dir = create_run_directory(experiment_dir, run_name)
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

    # Generate plots by default (skip with --no-report)
    if not args.no_report:
        results_csv = run_dir / "results.csv"
        if results_csv.exists():
            plot_paths = plot_keff(
                results_csv,
                output_dir=run_dir / "plots",
                safety_limit=template_class.SAFETY_LIMIT,
            )
            if plot_paths:
                print(f"\nPlots: {run_dir / 'plots'}")

    # Generate consultant package if requested
    if args.package:
        create_consultant_package(run_dir, experiment_dir, config)

    print(f"\nResults: {run_dir}")
    print(f"Latest:  {experiment_dir / 'runs' / run_name / 'latest'}")


def main():
    load_config()

    parser = argparse.ArgumentParser(description="Run criticality experiment")
    parser.add_argument("experiment", nargs="?", help="Path to experiment.yaml")
    parser.add_argument("--validate", action="store_true", help="Generate 2D geometry plots")
    parser.add_argument("--voxel", action="store_true", help="Generate 3D voxel PNG")
    parser.add_argument("--vti", action="store_true", help="Export .vti file for ParaView")
    parser.add_argument("--interactive", action="store_true", help="Launch PyVista interactive viewer")
    parser.add_argument("--case", help="Run specific case label")
    parser.add_argument("--solver", choices=["openmc", "mcnp", "all"], help="Override solver")
    parser.add_argument("--smoke", action="store_true", help="Quick smoke test")
    parser.add_argument("--name", help="Custom name for this run (default: YAML filename)")
    parser.add_argument("--no-report", action="store_true", help="Skip plot generation")
    parser.add_argument("--package", action="store_true", help="Generate consultant verification package")
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
