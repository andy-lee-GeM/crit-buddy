"""
Simple plotting utilities for criticality results.

Reads CSV directly and generates k-eff plots.
Supports:
- 1D line plots for single parameter sweeps
- 2D heatmaps for two-parameter sweeps
"""

from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd


# Solver colors and markers
SOLVER_STYLES = {
    "openmc": {"color": "#1f77b4", "marker": "o", "label": "OpenMC"},
    "mcnp": {"color": "#ff7f0e", "marker": "s", "label": "MCNP"},
}

# Status colors for heatmap
STATUS_COLORS = {
    "SAFE": "#2ecc71",      # Green
    "MARGINAL": "#f39c12",  # Orange
    "CRITICAL": "#e74c3c",  # Red
}


def plot_keff(
    results_csv: Path,
    output_dir: Optional[Path] = None,
    safety_limit: float = 0.95,
) -> List[Path]:
    """
    Generate k-eff vs parameter plots from results CSV.

    For single-parameter sweeps: creates a simple line plot.
    For two-parameter sweeps: creates grouped line plots where one parameter
    is on the X-axis and the other is shown as separate colored lines.

    Args:
        results_csv: Path to results.csv file
        output_dir: Directory to save plots (default: same as CSV)
        safety_limit: k-eff safety limit line value

    Returns:
        List of paths to generated plot files
    """
    results_csv = Path(results_csv)
    df = pd.read_csv(results_csv)

    if output_dir is None:
        output_dir = results_csv.parent / "plots"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find swept parameters (columns that aren't standard and have multiple values)
    standard_cols = {"case", "solver", "keff", "std", "keff_2sigma", "status", "execution_time"}
    param_cols = [c for c in df.columns if c not in standard_cols]

    swept_params = []
    for col in param_cols:
        if df[col].nunique() > 1:
            swept_params.append(col)

    if not swept_params:
        return []

    generated = []

    # Handle based on number of swept parameters
    if len(swept_params) == 1:
        # Single parameter sweep - simple line plot
        generated.extend(_plot_single_sweep(df, swept_params[0], output_dir, safety_limit))
    elif len(swept_params) == 2:
        # Two parameter sweep - grouped line plots
        # Create plot for each parameter as X-axis, grouped by the other
        for i, x_param in enumerate(swept_params):
            group_param = swept_params[1 - i]
            generated.extend(_plot_grouped_sweep(df, x_param, group_param, output_dir, safety_limit))
    else:
        # 3+ parameters - fall back to simple plots for each
        for param in swept_params:
            generated.extend(_plot_single_sweep(df, param, output_dir, safety_limit))

    return generated


def _plot_single_sweep(
    df: pd.DataFrame,
    param: str,
    output_dir: Path,
    safety_limit: float,
) -> List[Path]:
    """Create simple line plot for single-parameter sweep."""
    solvers = df["solver"].unique().tolist()
    generated = []

    fig, ax = plt.subplots(figsize=(10, 6))

    for solver in solvers:
        solver_df = df[df["solver"] == solver].sort_values(param)
        style = SOLVER_STYLES.get(solver, {"color": "#2ca02c", "marker": "^", "label": solver.upper()})

        ax.errorbar(
            solver_df[param],
            solver_df["keff"],
            yerr=2 * solver_df["std"],
            fmt=f"{style['marker']}-",
            color=style["color"],
            label=style["label"],
            capsize=4,
            markersize=8,
            linewidth=2,
        )

    # Safety limit lines
    ax.axhline(y=safety_limit, color="red", linestyle="--", linewidth=2,
               label=f"Safety Limit ({safety_limit})", alpha=0.7)
    ax.axhline(y=1.0, color="darkred", linestyle="-", linewidth=1.5,
               label="Critical (1.0)", alpha=0.5)

    ax.set_xlabel(_format_param_label(param), fontsize=12, fontweight="bold")
    ax.set_ylabel("k-eff", fontsize=12, fontweight="bold")
    ax.set_title(f"k-eff vs {_format_param_label(param)}", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = output_dir / f"keff_vs_{param}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    generated.append(output_path)
    return generated


def _plot_grouped_sweep(
    df: pd.DataFrame,
    x_param: str,
    group_param: str,
    output_dir: Path,
    safety_limit: float,
) -> List[Path]:
    """Create grouped line plot with separate colored lines for each group value."""
    generated = []

    # Use first solver if multiple
    solver = df["solver"].iloc[0]
    solver_df = df[df["solver"] == solver]

    # Get unique values for grouping
    group_values = sorted(solver_df[group_param].unique())
    n_groups = len(group_values)

    # Color palette
    colors = plt.cm.viridis(np.linspace(0.15, 0.85, n_groups))

    fig, ax = plt.subplots(figsize=(10, 7))

    for i, group_val in enumerate(group_values):
        group_df = solver_df[solver_df[group_param] == group_val].sort_values(x_param)

        # Format label based on parameter type
        if group_param == "enrichment":
            label = f"{group_val}% enrichment"
        elif group_param in {"h_to_u_ratio", "h_to_u"}:
            label = f"H/U = {group_val}"
        elif group_param == "fill_fraction":
            label = f"{group_val*100:.0f}% fill"
        else:
            label = f"{group_param} = {group_val}"

        ax.errorbar(
            group_df[x_param],
            group_df["keff"],
            yerr=2 * group_df["std"],
            fmt="o-",
            color=colors[i],
            label=label,
            capsize=4,
            markersize=8,
            linewidth=2,
        )

    # Safety limit lines
    ax.axhline(y=safety_limit, color="red", linestyle="--", linewidth=2,
               label=f"Safety Limit (k={safety_limit})", alpha=0.8)
    ax.axhline(y=1.0, color="darkred", linestyle="-", linewidth=2,
               label="Critical (k=1.0)", alpha=0.6)

    ax.set_xlabel(_format_param_label(x_param), fontsize=12, fontweight="bold")
    ax.set_ylabel("k-effective", fontsize=12, fontweight="bold")
    ax.set_title(f"k-eff vs {_format_param_label(x_param)} by {_format_param_label(group_param)}",
                 fontsize=14, fontweight="bold")
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)

    # Set reasonable y-axis limits
    ymin = max(0.4, solver_df["keff"].min() - 0.1)
    ymax = min(1.5, solver_df["keff"].max() + 0.1)
    ax.set_ylim(ymin, ymax)

    plt.tight_layout()

    output_path = output_dir / f"keff_vs_{x_param}_by_{group_param}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    generated.append(output_path)
    return generated


def _format_param_label(param: str) -> str:
    """Format parameter name for display on plots."""
    labels = {
        "enrichment": "Enrichment (%)",
        "fill_fraction": "Fill Fraction",
        "h_to_u_ratio": "H/U Ratio",
        "h_to_u": "H/U Ratio",
        "gap_xy_cm": "Gap Distance (cm)",
        "gap_z_cm": "Vertical Gap (cm)",
        "radius_cm": "Radius (cm)",
        "height_cm": "Height (cm)",
    }
    return labels.get(param, param.replace("_", " ").title())


def plot_heatmap(
    results_csv: Path,
    output_dir: Optional[Path] = None,
    safety_limit: float = 0.95,
) -> List[Path]:
    """
    Generate 2D heatmap for two-parameter sweeps.

    Args:
        results_csv: Path to results.csv file
        output_dir: Directory to save plots (default: same as CSV)
        safety_limit: k-eff safety limit for contour line

    Returns:
        List of paths to generated heatmap files
    """
    results_csv = Path(results_csv)
    df = pd.read_csv(results_csv)

    if output_dir is None:
        output_dir = results_csv.parent / "plots"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find swept parameters
    standard_cols = {"case", "solver", "keff", "std", "keff_2sigma", "status", "execution_time"}
    param_cols = [c for c in df.columns if c not in standard_cols]

    swept_params = []
    for col in param_cols:
        if df[col].nunique() > 1:
            swept_params.append(col)

    # Need exactly 2 swept parameters for heatmap
    if len(swept_params) != 2:
        return []

    param_x, param_y = swept_params[0], swept_params[1]

    # Use first solver if multiple
    solver = df["solver"].iloc[0]
    solver_df = df[df["solver"] == solver]

    generated = []

    # Get unique values for each parameter
    x_vals = sorted(solver_df[param_x].unique())
    y_vals = sorted(solver_df[param_y].unique())

    # Create 2D grid for k-eff values
    keff_grid = np.zeros((len(y_vals), len(x_vals)))
    keff_grid[:] = np.nan

    for _, row in solver_df.iterrows():
        xi = x_vals.index(row[param_x])
        yi = y_vals.index(row[param_y])
        keff_grid[yi, xi] = row["keff"]

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 9))

    # Custom colormap: green (safe) -> yellow -> orange -> red (critical)
    colors_list = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#8b0000"]
    n_bins = 100
    cmap = mcolors.LinearSegmentedColormap.from_list("criticality", colors_list, N=n_bins)

    # Determine color scale bounds
    vmin = max(0.5, np.nanmin(keff_grid) - 0.05)
    vmax = min(2.0, np.nanmax(keff_grid) + 0.05)

    # Plot heatmap
    im = ax.imshow(
        keff_grid,
        cmap=cmap,
        aspect="auto",
        origin="lower",
        extent=[min(x_vals) - 0.5, max(x_vals) + 0.5, min(y_vals) - 0.5, max(y_vals) + 0.5],
        vmin=vmin,
        vmax=vmax,
    )

    # Add contour lines at safety limit and critical
    X, Y = np.meshgrid(x_vals, y_vals)

    # Safety limit contour (k=0.95)
    try:
        cs1 = ax.contour(X, Y, keff_grid, levels=[safety_limit], colors=["white"], linewidths=[3], linestyles=["--"])
        ax.clabel(cs1, inline=True, fontsize=10, fmt=f"k={safety_limit}")
    except ValueError:
        pass  # No contour if all values above/below

    # Critical contour (k=1.0)
    try:
        cs2 = ax.contour(X, Y, keff_grid, levels=[1.0], colors=["black"], linewidths=[2], linestyles=["-"])
        ax.clabel(cs2, inline=True, fontsize=10, fmt="k=1.0")
    except ValueError:
        pass

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("k-eff", fontsize=12, fontweight="bold")

    # Add horizontal lines at safety limit and critical on colorbar
    cbar.ax.axhline(y=(safety_limit - vmin) / (vmax - vmin), color="white", linewidth=2, linestyle="--")
    cbar.ax.axhline(y=(1.0 - vmin) / (vmax - vmin), color="black", linewidth=2, linestyle="-")

    # Labels and title
    ax.set_xlabel(param_x.replace("_", " ").title(), fontsize=14, fontweight="bold")
    ax.set_ylabel(param_y.replace("_", " ").title(), fontsize=14, fontweight="bold")
    ax.set_title(f"k-eff Heatmap: {param_y.replace('_', ' ').title()} vs {param_x.replace('_', ' ').title()}",
                 fontsize=16, fontweight="bold")

    # Set tick labels
    ax.set_xticks(x_vals)
    ax.set_yticks(y_vals)

    # Add grid
    ax.grid(True, alpha=0.3, color="white", linewidth=0.5)

    # Add text annotations for each cell
    for i, y in enumerate(y_vals):
        for j, x in enumerate(x_vals):
            val = keff_grid[i, j]
            if not np.isnan(val):
                # Choose text color based on background
                text_color = "white" if val > 1.2 else "black"
                ax.text(x, y, f"{val:.3f}", ha="center", va="center",
                       fontsize=8, color=text_color, fontweight="bold")

    plt.tight_layout()

    output_path = output_dir / f"heatmap_{param_x}_vs_{param_y}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    generated.append(output_path)

    # Also create a status heatmap (SAFE/MARGINAL/CRITICAL)
    fig2, ax2 = plt.subplots(figsize=(12, 9))

    # Create status grid
    status_grid = np.zeros((len(y_vals), len(x_vals)))
    for _, row in solver_df.iterrows():
        xi = x_vals.index(row[param_x])
        yi = y_vals.index(row[param_y])
        k2sigma = row["keff_2sigma"]
        if k2sigma < safety_limit:
            status_grid[yi, xi] = 0  # SAFE
        elif k2sigma < 1.0:
            status_grid[yi, xi] = 1  # MARGINAL
        else:
            status_grid[yi, xi] = 2  # CRITICAL

    # Status colormap
    status_cmap = mcolors.ListedColormap(["#2ecc71", "#f39c12", "#e74c3c"])
    bounds = [-0.5, 0.5, 1.5, 2.5]
    norm = mcolors.BoundaryNorm(bounds, status_cmap.N)

    im2 = ax2.imshow(
        status_grid,
        cmap=status_cmap,
        norm=norm,
        aspect="auto",
        origin="lower",
        extent=[min(x_vals) - 0.5, max(x_vals) + 0.5, min(y_vals) - 0.5, max(y_vals) + 0.5],
    )

    # Colorbar with status labels
    cbar2 = plt.colorbar(im2, ax=ax2, shrink=0.8, ticks=[0, 1, 2])
    cbar2.ax.set_yticklabels(["SAFE", "MARGINAL", "CRITICAL"])
    cbar2.set_label("Status", fontsize=12, fontweight="bold")

    ax2.set_xlabel(param_x.replace("_", " ").title(), fontsize=14, fontweight="bold")
    ax2.set_ylabel(param_y.replace("_", " ").title(), fontsize=14, fontweight="bold")
    ax2.set_title(f"Safety Status: {param_y.replace('_', ' ').title()} vs {param_x.replace('_', ' ').title()}",
                  fontsize=16, fontweight="bold")

    ax2.set_xticks(x_vals)
    ax2.set_yticks(y_vals)
    ax2.grid(True, alpha=0.3, color="white", linewidth=0.5)

    plt.tight_layout()

    output_path2 = output_dir / f"status_{param_x}_vs_{param_y}.png"
    plt.savefig(output_path2, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig2)

    generated.append(output_path2)

    return generated


def plot_keff_vs_gap_by_enrichment(
    results_csv: Path,
    output_path: Optional[Path] = None,
    safety_limit: float = 0.95,
    gap_param: str = "gap_xy_cm",
    group_param: str = "enrichment",
) -> Path:
    """
    Generate line plot of k-eff vs gap with separate lines for each enrichment.

    Args:
        results_csv: Path to results.csv file
        output_path: Path for output plot file
        safety_limit: k-eff safety limit line value
        gap_param: Column name for gap parameter (x-axis)
        group_param: Column name for grouping parameter (separate lines)

    Returns:
        Path to generated plot file
    """
    results_csv = Path(results_csv)
    df = pd.read_csv(results_csv)

    if output_path is None:
        output_path = results_csv.parent / "plots" / f"keff_vs_{gap_param}_by_{group_param}.png"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Color palette for different enrichments
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, df[group_param].nunique()))

    fig, ax = plt.subplots(figsize=(10, 7))

    for i, group_val in enumerate(sorted(df[group_param].unique())):
        group_df = df[df[group_param] == group_val].sort_values(gap_param)

        ax.errorbar(
            group_df[gap_param],
            group_df["keff"],
            yerr=2 * group_df["std"],
            fmt="o-",
            color=colors[i],
            label=f"{group_val}% enrichment",
            capsize=4,
            markersize=8,
            linewidth=2,
        )

    # Safety limit lines
    ax.axhline(y=safety_limit, color="red", linestyle="--", linewidth=2,
               label=f"Safety Limit (k={safety_limit})", alpha=0.8)
    ax.axhline(y=1.0, color="darkred", linestyle="-", linewidth=2,
               label="Critical (k=1.0)", alpha=0.6)

    ax.set_xlabel("Gap Distance (cm)", fontsize=12, fontweight="bold")
    ax.set_ylabel("k-effective", fontsize=12, fontweight="bold")
    ax.set_title("k-effective vs Gap Distance by Enrichment", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)

    # Set reasonable y-axis limits
    ymin = max(0.4, df["keff"].min() - 0.1)
    ymax = min(1.3, df["keff"].max() + 0.1)
    ax.set_ylim(ymin, ymax)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    return output_path
