"""
Report generation orchestration.

Generates complete standard reports from study results.
"""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt

from .data import StudyResults
from .tables import results_table, comparison_table, summary_table
from .plots import generate_all_parameter_plots, solver_comparison_plot


def generate_report(
    results_csv: Path,
    output_dir: Optional[Path] = None,
    safety_limit: float = 0.95,
    format: str = "console",
) -> str:
    """
    Generate a complete standard report from results CSV.

    Args:
        results_csv: Path to results.csv file
        output_dir: Directory for output files (plots, markdown).
                   If None, uses same directory as CSV.
        safety_limit: k-eff safety limit for plots
        format: "console" for terminal output, "markdown" for .md file

    Returns:
        Report text (console or markdown format)
    """
    results_csv = Path(results_csv)

    if output_dir is None:
        output_dir = results_csv.parent
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load results
    results = StudyResults.from_csv(results_csv)

    # Build report sections
    sections = []

    # Header
    if format == "markdown":
        sections.append("# Criticality Study Report\n")
    else:
        sections.append("=" * 60)
        sections.append("           CRITICALITY STUDY REPORT")
        sections.append("=" * 60)

    # Summary
    sections.append("")
    sections.append(summary_table(results, format=format))

    # Results table
    sections.append("")
    if format == "markdown":
        sections.append("## Results\n")
    else:
        sections.append("\nRESULTS TABLE")
        sections.append("-" * 40)
    sections.append(results_table(results, format=format))

    # Comparison table (if multiple solvers)
    if results.has_multiple_solvers:
        sections.append("")
        if format == "markdown":
            sections.append("## Solver Comparison\n")
        else:
            sections.append("\nSOLVER COMPARISON")
            sections.append("-" * 40)
        sections.append(comparison_table(results, format=format))

    # Generate plots
    if results.swept_params:
        plots_dir = output_dir / "plots"
        plot_paths = generate_all_parameter_plots(
            results,
            plots_dir,
            safety_limit=safety_limit,
        )

        sections.append("")
        if format == "markdown":
            sections.append("## Parameter Plots\n")
            for path in plot_paths:
                rel_path = path.relative_to(output_dir)
                param = path.stem.replace("keff_vs_", "")
                sections.append(f"### k-eff vs {param}\n")
                sections.append(f"![k-eff vs {param}]({rel_path})\n")
        else:
            sections.append("\nPARAMETER PLOTS")
            sections.append("-" * 40)
            for path in plot_paths:
                sections.append(f"  Generated: {path}")

    # Solver comparison plot
    if results.has_multiple_solvers:
        comp_plot_path = output_dir / "plots" / "solver_comparison.png"
        comp_plot_path.parent.mkdir(parents=True, exist_ok=True)

        fig = solver_comparison_plot(results, output_path=comp_plot_path)
        if fig:
            plt.close(fig)

            if format == "markdown":
                rel_path = comp_plot_path.relative_to(output_dir)
                sections.append(f"\n### Solver Comparison\n")
                sections.append(f"![Solver Comparison]({rel_path})\n")
            else:
                sections.append(f"  Generated: {comp_plot_path}")

    report_text = "\n".join(sections)

    # Write markdown file if requested
    if format == "markdown":
        report_path = output_dir / "report.md"
        with open(report_path, "w") as f:
            f.write(report_text)
        print(f"Report written to: {report_path}")

    return report_text


def print_report(results_csv: Path, safety_limit: float = 0.95) -> None:
    """
    Print report to console.

    Args:
        results_csv: Path to results.csv file
        safety_limit: k-eff safety limit for plots
    """
    report = generate_report(
        results_csv,
        safety_limit=safety_limit,
        format="console",
    )
    print(report)


def save_report(
    results_csv: Path,
    output_dir: Optional[Path] = None,
    safety_limit: float = 0.95,
) -> Path:
    """
    Generate and save markdown report with plots.

    Args:
        results_csv: Path to results.csv file
        output_dir: Directory for output files
        safety_limit: k-eff safety limit for plots

    Returns:
        Path to generated report.md
    """
    results_csv = Path(results_csv)

    if output_dir is None:
        output_dir = results_csv.parent

    generate_report(
        results_csv,
        output_dir=output_dir,
        safety_limit=safety_limit,
        format="markdown",
    )

    return output_dir / "report.md"
