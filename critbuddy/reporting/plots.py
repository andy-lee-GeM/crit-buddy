"""
Simple plotting utilities for criticality results.

Reads CSV directly and generates k-eff plots.
"""

from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import pandas as pd


# Solver colors and markers
SOLVER_STYLES = {
    "openmc": {"color": "#1f77b4", "marker": "o", "label": "OpenMC"},
    "mcnp": {"color": "#ff7f0e", "marker": "s", "label": "MCNP"},
}


def plot_keff(
    results_csv: Path,
    output_dir: Optional[Path] = None,
    safety_limit: float = 0.95,
) -> List[Path]:
    """
    Generate k-eff vs parameter plots from results CSV.

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

    solvers = df["solver"].unique().tolist()
    generated = []

    for param in swept_params:
        fig, ax = plt.subplots(figsize=(10, 6))

        for solver in solvers:
            solver_df = df[df["solver"] == solver].sort_values(param)
            style = SOLVER_STYLES.get(solver, {"color": "#2ca02c", "marker": "^", "label": solver.upper()})

            ax.errorbar(
                solver_df[param],
                solver_df["keff"],
                yerr=2 * solver_df["std"],
                fmt=style["marker"],
                color=style["color"],
                label=style["label"],
                capsize=4,
                markersize=8,
                linewidth=1.5,
            )

            ax.plot(
                solver_df[param],
                solver_df["keff"],
                color=style["color"],
                alpha=0.5,
                linestyle="--",
            )

        # Safety limit lines
        ax.axhline(y=safety_limit, color="red", linestyle="--", linewidth=2,
                   label=f"Safety Limit ({safety_limit})", alpha=0.7)
        ax.axhline(y=1.0, color="darkred", linestyle="-", linewidth=1.5,
                   label="Critical (1.0)", alpha=0.5)

        ax.set_xlabel(param, fontsize=12, fontweight="bold")
        ax.set_ylabel("k-eff", fontsize=12, fontweight="bold")
        ax.set_title(f"k-eff vs {param}", fontsize=14, fontweight="bold")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        output_path = output_dir / f"keff_vs_{param}.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        generated.append(output_path)

    return generated
