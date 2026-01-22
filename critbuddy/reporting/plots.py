"""
Plotting utilities for results reporting.

Generates k-eff vs parameter plots for swept parameters.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

from .data import StudyResults


# Solver colors and markers
SOLVER_STYLES = {
    "openmc": {"color": "#1f77b4", "marker": "o", "label": "OpenMC"},
    "mcnp": {"color": "#ff7f0e", "marker": "s", "label": "MCNP"},
}

DEFAULT_STYLE = {"color": "#2ca02c", "marker": "^", "label": None}


def get_solver_style(solver: str) -> dict:
    """Get plotting style for a solver."""
    style = SOLVER_STYLES.get(solver, DEFAULT_STYLE).copy()
    if style["label"] is None:
        style["label"] = solver.upper()
    return style


def keff_vs_parameter_plot(
    results: StudyResults,
    param: str,
    output_path: Optional[Path] = None,
    safety_limit: float = 0.95,
    show_limit: bool = True,
    figsize: Tuple[float, float] = (10, 6),
) -> plt.Figure:
    """
    Generate k-eff vs parameter plot for a single swept parameter.

    Args:
        results: StudyResults object
        param: Parameter name to plot on x-axis
        output_path: If provided, save figure to this path
        safety_limit: k-eff safety limit line value
        show_limit: Whether to show safety limit line
        figsize: Figure size in inches

    Returns:
        matplotlib Figure object
    """
    if param not in results.swept_params:
        raise ValueError(f"Parameter '{param}' is not a swept parameter. "
                        f"Swept params: {results.swept_params}")

    fig, ax = plt.subplots(figsize=figsize)
    df = results.data

    # Plot each solver
    for solver in results.solvers:
        solver_df = df[df["solver"] == solver].copy()
        solver_df = solver_df.sort_values(param)

        style = get_solver_style(solver)

        # Plot with error bars (2-sigma)
        ax.errorbar(
            solver_df[param],
            solver_df["keff"],
            yerr=2 * solver_df["std"],
            fmt=style["marker"],
            color=style["color"],
            label=style["label"],
            capsize=4,
            capthick=1.5,
            markersize=8,
            linewidth=1.5,
            elinewidth=1.5,
        )

        # Connect points with line
        ax.plot(
            solver_df[param],
            solver_df["keff"],
            color=style["color"],
            alpha=0.5,
            linewidth=1,
            linestyle="--",
        )

    # Safety limit line
    if show_limit:
        ax.axhline(
            y=safety_limit,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Safety Limit ({safety_limit})",
            alpha=0.7,
        )

        # Critical line at 1.0
        ax.axhline(
            y=1.0,
            color="darkred",
            linestyle="-",
            linewidth=1.5,
            label="Critical (1.0)",
            alpha=0.5,
        )

    # Labels and formatting
    ax.set_xlabel(param, fontsize=12, fontweight="bold")
    ax.set_ylabel("k-eff", fontsize=12, fontweight="bold")
    ax.set_title(f"k-eff vs {param}", fontsize=14, fontweight="bold")

    ax.legend(loc="best", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # Add fixed params as subtitle if any
    if results.fixed_params:
        fixed_str = ", ".join(f"{k}={v}" for k, v in results.fixed_params.items())
        ax.text(
            0.5, -0.12,
            f"Fixed: {fixed_str}",
            transform=ax.transAxes,
            ha="center",
            fontsize=9,
            style="italic",
            alpha=0.7,
        )

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")

    return fig


def generate_all_parameter_plots(
    results: StudyResults,
    output_dir: Path,
    safety_limit: float = 0.95,
    format: str = "png",
) -> List[Path]:
    """
    Generate k-eff plots for all swept parameters.

    Args:
        results: StudyResults object
        output_dir: Directory to save plots
        safety_limit: k-eff safety limit line value
        format: Image format (png, pdf, svg)

    Returns:
        List of paths to generated plot files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = []

    for param in results.swept_params:
        output_path = output_dir / f"keff_vs_{param}.{format}"

        fig = keff_vs_parameter_plot(
            results,
            param,
            output_path=output_path,
            safety_limit=safety_limit,
        )
        plt.close(fig)

        generated.append(output_path)

    return generated


def solver_comparison_plot(
    results: StudyResults,
    output_path: Optional[Path] = None,
    figsize: Tuple[float, float] = (10, 6),
) -> Optional[plt.Figure]:
    """
    Generate solver comparison scatter plot (OpenMC vs MCNP).

    Args:
        results: StudyResults object
        output_path: If provided, save figure to this path
        figsize: Figure size in inches

    Returns:
        matplotlib Figure object, or None if comparison not possible
    """
    if not results.has_multiple_solvers:
        return None

    if "openmc" not in results.solvers or "mcnp" not in results.solvers:
        return None

    comp_df = results.get_comparison_data()

    fig, ax = plt.subplots(figsize=figsize)

    # Scatter plot
    ax.errorbar(
        comp_df["mcnp_keff"],
        comp_df["openmc_keff"],
        xerr=2 * comp_df["mcnp_std"],
        yerr=2 * comp_df["openmc_std"],
        fmt="o",
        color="#1f77b4",
        capsize=3,
        markersize=8,
        alpha=0.7,
    )

    # Perfect agreement line
    keff_min = min(comp_df["mcnp_keff"].min(), comp_df["openmc_keff"].min())
    keff_max = max(comp_df["mcnp_keff"].max(), comp_df["openmc_keff"].max())
    margin = 0.01
    line_range = [keff_min - margin, keff_max + margin]

    ax.plot(line_range, line_range, "k--", linewidth=1.5, label="Perfect Agreement")

    # Labels
    ax.set_xlabel("MCNP k-eff", fontsize=12, fontweight="bold")
    ax.set_ylabel("OpenMC k-eff", fontsize=12, fontweight="bold")
    ax.set_title("Solver Comparison: OpenMC vs MCNP", fontsize=14, fontweight="bold")

    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")

    return fig
