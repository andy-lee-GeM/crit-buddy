"""
Simple plotting utilities for criticality results.

Reads a single results CSV and generates either:
- one explicit line diagram via the CLI/helpers below
- multiple default line plots for internal runner use
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SOLVER_STYLES = {
    "openmc": {"color": "#1f77b4", "marker": "o", "label": "OpenMC"},
    "mcnp": {"color": "#ff7f0e", "marker": "s", "label": "MCNP"},
}

STANDARD_COLS = {"case", "solver", "keff", "std", "keff_2sigma", "status", "execution_time"}


def plot_keff(
    results_csv: Path,
    output_dir: Path | None = None,
    safety_limit: float = 0.95,
) -> list[Path]:
    """
    Generate default k-eff plots for a run.

    This is the multi-plot runner-facing helper. For one explicit diagram, use
    `plot_keff_diagram()`.
    """
    results_csv = Path(results_csv)
    df = _load_results_frame(results_csv)
    output_dir = _resolve_output_dir(results_csv, output_dir)
    swept_params = _find_swept_params(df)

    if not swept_params:
        return []

    generated: list[Path] = []
    if len(swept_params) == 1:
        param = swept_params[0]
        output_path = output_dir / f"keff_vs_{param}.png"
        _save_single_sweep_plot(df, param, output_path, safety_limit=safety_limit)
        generated.append(output_path)
    elif len(swept_params) == 2:
        if _are_one_to_one_companions(df, swept_params[0], swept_params[1]):
            for param in swept_params:
                output_path = output_dir / f"keff_vs_{param}.png"
                _save_single_sweep_plot(df, param, output_path, safety_limit=safety_limit)
                generated.append(output_path)
        else:
            for index, x_param in enumerate(swept_params):
                group_param = swept_params[1 - index]
                output_path = output_dir / f"keff_vs_{x_param}_by_{group_param}.png"
                _save_grouped_sweep_plot(
                    df,
                    x_param,
                    group_param,
                    output_path,
                    safety_limit=safety_limit,
                )
                generated.append(output_path)
    else:
        for param in swept_params:
            output_path = output_dir / f"keff_vs_{param}.png"
            _save_single_sweep_plot(df, param, output_path, safety_limit=safety_limit)
            generated.append(output_path)

    return generated


def plot_keff_diagram(
    results_csv: str | Path,
    output_path: str | Path,
    *,
    x_param: str | None = None,
    group_param: str | None = None,
    safety_limit: float = 0.95,
    title: str | None = None,
) -> Path:
    """Generate one line plot from one results CSV."""
    results_csv = Path(results_csv)
    output_path = Path(output_path)
    df = _load_results_frame(results_csv)
    swept_params = _find_swept_params(df)
    x_param, group_param = _resolve_line_plot_params(
        df,
        swept_params,
        x_param=x_param,
        group_param=group_param,
    )

    if group_param is None:
        _save_single_sweep_plot(df, x_param, output_path, safety_limit=safety_limit, title=title)
    else:
        _save_grouped_sweep_plot(
            df,
            x_param,
            group_param,
            output_path,
            safety_limit=safety_limit,
            title=title,
        )

    return output_path


def _load_results_frame(results_csv: Path) -> pd.DataFrame:
    return pd.read_csv(results_csv)


def _resolve_output_dir(results_csv: Path, output_dir: Path | None) -> Path:
    if output_dir is None:
        output_dir = results_csv.parent / "plots"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _find_swept_params(df: pd.DataFrame) -> list[str]:
    return [column for column in df.columns if column not in STANDARD_COLS and df[column].nunique() > 1]


def _resolve_line_plot_params(
    df: pd.DataFrame,
    swept_params: Sequence[str],
    *,
    x_param: str | None,
    group_param: str | None,
) -> tuple[str, str | None]:
    if not swept_params:
        raise ValueError("No swept parameters found in results.csv")

    if x_param is not None and x_param not in swept_params:
        raise ValueError(f"x parameter '{x_param}' is not a swept parameter: {sorted(swept_params)}")

    if group_param is not None and group_param not in swept_params:
        raise ValueError(f"group parameter '{group_param}' is not a swept parameter: {sorted(swept_params)}")

    if len(swept_params) == 1:
        if group_param is not None:
            raise ValueError("group_param cannot be used when only one parameter is swept")
        return swept_params[0], None

    if x_param is None and group_param is None:
        raise ValueError(
            "Line plot is ambiguous for multi-parameter results.csv; specify --x and optionally --group-by"
        )

    if x_param is None:
        remaining = [param for param in swept_params if param != group_param]
        if len(remaining) != 1:
            raise ValueError("Could not infer x parameter uniquely")
        x_param = remaining[0]

    if group_param is None:
        remaining = [param for param in swept_params if param != x_param]
        if not remaining:
            return x_param, None
        if all(_are_one_to_one_companions(df, x_param, param) for param in remaining):
            return x_param, None
        if len(remaining) > 1:
            raise ValueError(
                "Line plot needs an explicit --group-by when more than one additional parameter is swept"
            )
        group_param = remaining[0]

    extra = [param for param in swept_params if param not in {x_param, group_param}]
    if extra:
        raise ValueError(
            "Line plot only supports one x parameter and one grouping parameter; extra swept parameters found: "
            + ", ".join(extra)
        )

    return x_param, group_param


def _save_single_sweep_plot(
    df: pd.DataFrame,
    param: str,
    output_path: Path,
    *,
    safety_limit: float,
    title: str | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))

    for solver in df["solver"].unique().tolist():
        solver_df = df[df["solver"] == solver].sort_values(param)
        style = SOLVER_STYLES.get(solver, {"color": "#2ca02c", "marker": "^", "label": solver.upper()})
        ax.errorbar(
            solver_df[param],
            solver_df["keff"],
            yerr=2 * solver_df["std"],
            fmt="o-",
            color=style["color"],
            label=style["label"],
            capsize=4,
            markersize=6,
            linewidth=2,
        )

    ax.axhline(y=safety_limit, color="red", linestyle="--", linewidth=2, label=f"Safety Limit ({safety_limit})", alpha=0.7)
    ax.axhline(y=1.0, color="darkred", linestyle="-", linewidth=1.5, label="Critical (1.0)", alpha=0.5)
    ax.set_xlabel(_format_param_label(param), fontsize=12, fontweight="bold")
    ax.set_ylabel("k-eff", fontsize=12, fontweight="bold")
    ax.set_title(title or f"k-eff vs {_format_param_label(param)}", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _save_grouped_sweep_plot(
    df: pd.DataFrame,
    x_param: str,
    group_param: str,
    output_path: Path,
    *,
    safety_limit: float,
    title: str | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    solver_df = _single_solver_frame(df)
    group_values = sorted(solver_df[group_param].unique())
    colors = plt.cm.viridis(np.linspace(0.15, 0.85, len(group_values)))
    fig, ax = plt.subplots(figsize=(10, 7))

    for index, group_value in enumerate(group_values):
        group_df = solver_df[solver_df[group_param] == group_value].sort_values(x_param)
        ax.errorbar(
            group_df[x_param],
            group_df["keff"],
            yerr=2 * group_df["std"],
            fmt="o-",
            color=colors[index],
            label=_format_group_label(group_param, group_value),
            capsize=4,
            markersize=6,
            linewidth=2,
        )

    ax.axhline(y=safety_limit, color="red", linestyle="--", linewidth=2, label=f"Safety Limit (k={safety_limit})", alpha=0.8)
    ax.axhline(y=1.0, color="darkred", linestyle="-", linewidth=2, label="Critical (k=1.0)", alpha=0.6)
    ax.set_xlabel(_format_param_label(x_param), fontsize=12, fontweight="bold")
    ax.set_ylabel("k-effective", fontsize=12, fontweight="bold")
    ax.set_title(
        title or f"k-eff vs {_format_param_label(x_param)} by {_format_param_label(group_param)}",
        fontsize=14,
        fontweight="bold",
    )
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(max(0.4, solver_df["keff"].min() - 0.1), min(1.5, solver_df["keff"].max() + 0.1))

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

def _single_solver_frame(df: pd.DataFrame) -> pd.DataFrame:
    solver = df["solver"].iloc[0]
    return df[df["solver"] == solver]


def _are_one_to_one_companions(df: pd.DataFrame, left_param: str, right_param: str) -> bool:
    paired = df[[left_param, right_param]].drop_duplicates()
    left_unique = paired.groupby(left_param)[right_param].nunique()
    right_unique = paired.groupby(right_param)[left_param].nunique()
    return bool(not left_unique.empty and left_unique.max() == 1 and right_unique.max() == 1)


def _format_group_label(group_param: str, group_value: object) -> str:
    if group_param == "enrichment":
        return f"{group_value}% enrichment"
    if group_param in {"h_to_u_ratio", "h_to_u"}:
        return f"H/U = {group_value}"
    if group_param in {"fill_fraction", "fill_fraction_percent"}:
        return f"{group_value}% fill"
    return f"{group_param} = {group_value}"


def _format_param_label(param: str) -> str:
    labels = {
        "enrichment": "Enrichment (%)",
        "fill_fraction": "Fill Fraction",
        "fill_fraction_percent": "Fill Fraction (%)",
        "fill_height_cm": "Fill Height (cm)",
        "h_to_u_ratio": "H/U Ratio",
        "h_to_u": "H/U Ratio",
        "gap_xy_cm": "Gap Distance (cm)",
        "gap_z_cm": "Vertical Gap (cm)",
        "radius_cm": "Radius (cm)",
        "height_cm": "Height (cm)",
    }
    return labels.get(param, param.replace("_", " ").title())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a single plot from a crit-buddy results.csv")
    subparsers = parser.add_subparsers(dest="command", required=True)

    keff_parser = subparsers.add_parser("keff", help="Generate one k-eff line plot")
    keff_parser.add_argument("results_csv", help="Path to results.csv")
    keff_parser.add_argument("--output", required=True, help="Path to output PNG")
    keff_parser.add_argument("--x", dest="x_param", help="Swept parameter to use on the x-axis")
    keff_parser.add_argument("--group-by", dest="group_param", help="Optional grouping parameter for a grouped line plot")
    keff_parser.add_argument("--safety-limit", type=float, default=0.95, help="Administrative safety limit (default: 0.95)")
    keff_parser.add_argument("--title", help="Optional plot title override")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    output_path = plot_keff_diagram(
        args.results_csv,
        args.output,
        x_param=args.x_param,
        group_param=args.group_param,
        safety_limit=args.safety_limit,
        title=args.title,
    )

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
