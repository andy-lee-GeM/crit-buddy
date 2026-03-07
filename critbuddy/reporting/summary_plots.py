#!/usr/bin/env python3
"""
Standard Summary Plot Generator

Generates the 3 standard plots for ticket reports:
1. fill_sweep.png - k-eff vs fill fraction with critical threshold
2. hu_sweep.png - k-eff vs H/U ratio showing peak moderation
3. geometry_comparison.png - UF6 vs UO2F2 bar chart

Usage:
    from critbuddy.reporting.summary_plots import generate_summary_plots

    generate_summary_plots("experiments/crit_requests/CR-008_pipe_array_3d")
"""

import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional


# Style settings
plt.style.use('seaborn-v0_8-whitegrid')
SAFE_COLOR = '#2ecc71'
MARGINAL_COLOR = '#f39c12'
CRITICAL_COLOR = '#e74c3c'


def load_results(results_csv: Path) -> List[Dict[str, Any]]:
    """Load results from CSV file."""
    if not results_csv.exists():
        return []
    with open(results_csv, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def find_latest_run(run_dir: Path) -> Optional[Path]:
    """Find the latest run directory."""
    if not run_dir.exists():
        return None
    latest_link = run_dir / "latest"
    if latest_link.exists():
        return latest_link
    dirs = [d for d in run_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
    if not dirs:
        return None
    return max(dirs, key=lambda d: d.name)


def get_status_color(keff_2sigma: float) -> str:
    """Get color based on k-eff value."""
    if keff_2sigma < 0.95:
        return SAFE_COLOR
    elif keff_2sigma < 1.0:
        return MARGINAL_COLOR
    else:
        return CRITICAL_COLOR


def plot_fill_sweep(results: List[Dict], output_path: Path, title: str = "Fill Fraction Sweep") -> None:
    """Plot k-eff vs fill fraction with critical threshold."""
    if not results:
        return

    # Extract data
    fill_fractions = [float(r['fill_fraction']) * 100 for r in results]
    keff_2sigma = [float(r['keff_2sigma']) for r in results]

    # Sort by fill fraction
    sorted_data = sorted(zip(fill_fractions, keff_2sigma))
    fill_fractions, keff_2sigma = zip(*sorted_data)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data points with color by status
    colors = [get_status_color(k) for k in keff_2sigma]
    ax.scatter(fill_fractions, keff_2sigma, c=colors, s=120, zorder=5, edgecolors='black', linewidths=1)
    ax.plot(fill_fractions, keff_2sigma, 'b-', linewidth=2, alpha=0.7, zorder=4)

    # Critical threshold lines
    ax.axhline(y=1.0, color=CRITICAL_COLOR, linestyle='--', linewidth=2, label='Critical (k-eff = 1.0)')
    ax.axhline(y=0.95, color=MARGINAL_COLOR, linestyle='--', linewidth=2, label='Safe limit (k-eff = 0.95)')

    # Shade regions
    ymin, ymax = ax.get_ylim()
    ax.axhspan(0, 0.95, alpha=0.1, color=SAFE_COLOR)
    ax.axhspan(0.95, 1.0, alpha=0.1, color=MARGINAL_COLOR)
    ax.axhspan(1.0, max(ymax, 1.5), alpha=0.1, color=CRITICAL_COLOR)

    # Find and annotate critical threshold
    for i in range(len(fill_fractions) - 1):
        if keff_2sigma[i] < 1.0 <= keff_2sigma[i+1]:
            crit_fill = fill_fractions[i] + (fill_fractions[i+1] - fill_fractions[i]) * (1.0 - keff_2sigma[i]) / (keff_2sigma[i+1] - keff_2sigma[i])
            ax.axvline(x=crit_fill, color='gray', linestyle=':', linewidth=1.5, alpha=0.7)
            ax.annotate(f'Critical threshold\n~{crit_fill:.0f}% fill', xy=(crit_fill, 1.0),
                        xytext=(crit_fill + 10, 0.85), fontsize=10, ha='left',
                        arrowprops=dict(arrowstyle='->', color='gray'))
            break

    # Find and annotate safe limit
    for i, (f, k) in enumerate(zip(fill_fractions, keff_2sigma)):
        if k < 0.95:
            ax.axvline(x=f, color=SAFE_COLOR, linestyle=':', linewidth=2)
            ax.annotate(f'Safe limit\n≤{f:.0f}% fill', xy=(f, k), xytext=(f - 8, k + 0.15),
                        fontsize=10, ha='center',
                        arrowprops=dict(arrowstyle='->', color=SAFE_COLOR))
            break

    ax.set_xlabel('Fill Fraction (%)', fontsize=12)
    ax.set_ylabel('k-eff + 2σ', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def plot_hu_sweep(results: List[Dict], output_path: Path, title: str = "H/U Ratio Sweep") -> None:
    """Plot k-eff vs H/U ratio showing peak moderation."""
    if not results:
        return

    # Extract data
    h_to_u = [int(float(r['h_to_u'])) for r in results]
    keff_2sigma = [float(r['keff_2sigma']) for r in results]

    # Sort by H/U
    sorted_data = sorted(zip(h_to_u, keff_2sigma))
    h_to_u, keff_2sigma = zip(*sorted_data)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot data
    colors = [get_status_color(k) for k in keff_2sigma]
    ax.scatter(h_to_u, keff_2sigma, c=colors, s=120, zorder=5, edgecolors='black', linewidths=1)
    ax.plot(h_to_u, keff_2sigma, 'b-', linewidth=2, alpha=0.7, zorder=4)

    # Critical threshold
    ax.axhline(y=1.0, color=CRITICAL_COLOR, linestyle='--', linewidth=2, label='Critical (k-eff = 1.0)')
    ax.axhline(y=0.95, color=MARGINAL_COLOR, linestyle='--', linewidth=2, label='Safe limit (k-eff = 0.95)')

    # Shade regions
    ymin, ymax = ax.get_ylim()
    ax.axhspan(0, 0.95, alpha=0.1, color=SAFE_COLOR)
    ax.axhspan(0.95, 1.0, alpha=0.1, color=MARGINAL_COLOR)
    ax.axhspan(1.0, max(ymax, 1.6), alpha=0.1, color=CRITICAL_COLOR)

    # Annotate peak
    peak_idx = keff_2sigma.index(max(keff_2sigma))
    peak_hu = h_to_u[peak_idx]
    peak_k = keff_2sigma[peak_idx]
    ax.annotate(f'Peak reactivity\nH/U = {peak_hu}', xy=(peak_hu, peak_k),
                xytext=(peak_hu - 15, peak_k - 0.15), fontsize=10, ha='center',
                arrowprops=dict(arrowstyle='->', color='gray'))

    ax.set_xlabel('H/U Ratio (Hydrogen-to-Uranium)', fontsize=12)
    ax.set_ylabel('k-eff + 2σ', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def plot_geometry_comparison(
    uf6_results: List[Dict],
    uo2f2_results: List[Dict],
    output_path: Path,
    swept_params: List[str],
    title: str = "Geometry Comparison: UF6 vs UO2F2"
) -> None:
    """Create bar chart comparing UF6 vs UO2F2 across geometries."""
    if not uf6_results or not uo2f2_results:
        return

    # Create geometry labels
    def make_label(row: Dict) -> str:
        parts = []
        for param in swept_params:
            if param in row:
                val = row[param]
                # Format nicely
                if param == "pipe_size":
                    parts.append(f'{val}"')
                elif param == "gap_cm":
                    parts.append(f'{val}cm')
                else:
                    parts.append(str(val))
        return " / ".join(parts)

    # Sort both result sets consistently
    def sort_key(row: Dict) -> tuple:
        return tuple(float(row.get(p, 0)) for p in swept_params)

    uf6_sorted = sorted(uf6_results, key=sort_key)
    uo2f2_sorted = sorted(uo2f2_results, key=sort_key)

    geometries = [make_label(r) for r in uf6_sorted]
    uf6_keff = [float(r['keff_2sigma']) for r in uf6_sorted]
    uo2f2_keff = [float(r['keff_2sigma']) for r in uo2f2_sorted]

    x = np.arange(len(geometries))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))

    # Bars
    bars1 = ax.bar(x - width/2, uf6_keff, width, label='UF6 Dry', color='steelblue', edgecolor='black')
    bars2 = ax.bar(x + width/2, uo2f2_keff, width, label='UO2F2 Wet', color='coral', edgecolor='black')

    # Critical lines
    ax.axhline(y=1.0, color=CRITICAL_COLOR, linestyle='--', linewidth=2, label='Critical (k=1.0)')
    ax.axhline(y=0.95, color=MARGINAL_COLOR, linestyle='--', linewidth=2, label='Safe (k=0.95)')

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{height:.2f}',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('Geometry', fontsize=12)
    ax.set_ylabel('k-eff + 2σ', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(geometries)
    ax.legend(loc='upper right')
    ax.set_ylim(0, max(max(uo2f2_keff) * 1.15, 1.2))
    ax.grid(True, alpha=0.3, axis='y')

    # Status annotations
    uf6_max = max(uf6_keff)
    uo2f2_max = max(uo2f2_keff)
    uf6_status = "SAFE" if uf6_max < 0.95 else "CRITICAL"
    uo2f2_status = "SAFE" if uo2f2_max < 0.95 else "CRITICAL"

    ax.text(0.02, 0.98, f'UF6: {uf6_status} (max k={uf6_max:.2f})', transform=ax.transAxes,
            fontsize=11, fontweight='bold', color='steelblue', verticalalignment='top')
    ax.text(0.02, 0.93, f'UO2F2: {uo2f2_status} (max k={uo2f2_max:.2f})', transform=ax.transAxes,
            fontsize=11, fontweight='bold', color='coral', verticalalignment='top')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def generate_summary_plots(
    experiment_dir: str,
    swept_params: Optional[List[str]] = None,
) -> Dict[str, Path]:
    """
    Generate all standard summary plots for an experiment.

    Args:
        experiment_dir: Path to experiment directory
        swept_params: List of swept parameter names (auto-detected if not provided)

    Returns:
        Dict mapping plot names to file paths
    """
    exp_path = Path(experiment_dir)
    runs_dir = exp_path / "runs"
    plots_dir = exp_path / "summary_plots"
    plots_dir.mkdir(exist_ok=True)

    generated = {}

    # Load results
    uf6_run = find_latest_run(runs_dir / "uf6")
    hu_run = find_latest_run(runs_dir / "uo2f2_hu_sweep")
    wet_run = find_latest_run(runs_dir / "uo2f2_wet")
    fill_run = find_latest_run(runs_dir / "uo2f2_fill_sweep")

    uf6_results = load_results(uf6_run / "results.csv") if uf6_run else []
    hu_results = load_results(hu_run / "results.csv") if hu_run else []
    wet_results = load_results(wet_run / "results.csv") if wet_run else []
    fill_results = load_results(fill_run / "results.csv") if fill_run else []

    # Auto-detect swept params if not provided
    if swept_params is None and uf6_results:
        swept_params = []
        for col in uf6_results[0].keys():
            if col in ['case', 'solver', 'keff', 'std', 'keff_2sigma', 'status', 'execution_time',
                       'enrichment', 'environment_material', 'environment_density', 'environment',
                       'fill_fraction', 'fissile_density',
                       'fissile_material', 'h_to_u', 'reflector_thickness_cm', 'wall_material']:
                continue
            unique_vals = set(r[col] for r in uf6_results)
            if len(unique_vals) > 1:
                swept_params.append(col)

    # Generate fill sweep plot
    if fill_results:
        output = plots_dir / "fill_sweep.png"
        plot_fill_sweep(fill_results, output, "Fill Fraction Sweep (Worst Case Geometry)")
        generated["fill_sweep"] = output

    # Generate H/U sweep plot
    if hu_results:
        output = plots_dir / "hu_sweep.png"
        plot_hu_sweep(hu_results, output, "H/U Ratio Sweep: Finding Peak Moderation")
        generated["hu_sweep"] = output

    # Generate geometry comparison
    if uf6_results and wet_results and swept_params:
        output = plots_dir / "geometry_comparison.png"
        plot_geometry_comparison(uf6_results, wet_results, output, swept_params,
                                 "Geometry Comparison: UF6 vs UO2F2 at 100% Fill")
        generated["geometry_comparison"] = output

    print(f"\nGenerated {len(generated)} plots in {plots_dir}")
    return generated


def plot_fill_sweep_overlay(
    results_by_geometry: Dict[str, List[Dict]],
    output_path: Path,
    title: str = "Fill Fraction Sweep - All Geometries"
) -> None:
    """
    Create overlay plot with one fill% curve per geometry.

    Each line represents a different geometry configuration, allowing
    comparison of critical thresholds across all geometries.

    Args:
        results_by_geometry: Dict mapping geometry label to results list
                            e.g. {"3\" pipe, gap=0": [...], "4\" pipe, gap=10": [...]}
        output_path: Path to save the plot
        title: Plot title
    """
    if not results_by_geometry:
        return

    fig, ax = plt.subplots(figsize=(12, 8))

    # Color palette for different geometries
    n_geometries = len(results_by_geometry)
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, n_geometries))

    # Track critical thresholds for annotation
    critical_thresholds = {}

    for i, (label, results) in enumerate(results_by_geometry.items()):
        if not results:
            continue

        fill_fractions = [float(r['fill_fraction']) * 100 for r in results]
        keff_2sigma = [float(r['keff_2sigma']) for r in results]

        # Sort by fill fraction
        sorted_data = sorted(zip(fill_fractions, keff_2sigma))
        fill_fractions, keff_2sigma = zip(*sorted_data)

        # Plot line
        ax.plot(fill_fractions, keff_2sigma, 'o-',
                color=colors[i], label=label, linewidth=2, markersize=6)

        # Find critical threshold (where k+2σ crosses 0.95)
        for j in range(len(fill_fractions) - 1):
            if keff_2sigma[j] < 0.95 <= keff_2sigma[j + 1]:
                # Linear interpolation
                crit_fill = fill_fractions[j] + (fill_fractions[j + 1] - fill_fractions[j]) * \
                           (0.95 - keff_2sigma[j]) / (keff_2sigma[j + 1] - keff_2sigma[j])
                critical_thresholds[label] = crit_fill
                break

    # Safety lines
    ax.axhline(y=0.95, color='orange', linestyle='--', linewidth=2,
               label='Safe limit (k+2σ = 0.95)')
    ax.axhline(y=1.0, color='red', linestyle='--', linewidth=2,
               label='Critical (k+2σ = 1.0)')

    # Shade regions
    ymin, ymax = ax.get_ylim()
    ax.axhspan(0, 0.95, alpha=0.05, color=SAFE_COLOR)
    ax.axhspan(0.95, 1.0, alpha=0.05, color=MARGINAL_COLOR)
    ax.axhspan(1.0, max(ymax, 1.5), alpha=0.05, color=CRITICAL_COLOR)

    ax.set_xlabel('Fill Fraction (%)', fontsize=12)
    ax.set_ylabel('k-eff + 2σ', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Position legend outside plot if many geometries
    if n_geometries > 6:
        ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5), fontsize=9)
    else:
        ax.legend(loc='best', fontsize=9)

    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 105)

    # Set y-axis limits
    all_keff = []
    for results in results_by_geometry.values():
        all_keff.extend([float(r['keff_2sigma']) for r in results])
    if all_keff:
        ymin = max(0.3, min(all_keff) - 0.1)
        ymax = min(1.8, max(all_keff) + 0.1)
        ax.set_ylim(ymin, ymax)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")

    # Print critical thresholds summary
    if critical_thresholds:
        print("\nCritical thresholds (k+2σ = 0.95):")
        for label, threshold in sorted(critical_thresholds.items(), key=lambda x: x[1]):
            print(f"  {label}: ~{threshold:.0f}% fill")


def generate_fill_overlay_from_runs(
    experiment_dir: str,
    output_path: Optional[Path] = None,
    title: str = "Fill Fraction Sweep - All Geometries",
) -> Optional[Path]:
    """
    Generate overlay fill% plot from multiple fill sweep runs.

    Looks for fill sweep results in runs/uo2f2_fill_sweep_*/ directories
    and creates an overlay plot with one curve per geometry.

    Args:
        experiment_dir: Path to experiment directory
        output_path: Output path for plot (default: summary_plots/fill_overlay.png)
        title: Plot title

    Returns:
        Path to generated plot, or None if no data found
    """
    exp_path = Path(experiment_dir)
    runs_dir = exp_path / "runs"

    if not runs_dir.exists():
        print(f"No runs directory found: {runs_dir}")
        return None

    # Find all fill sweep runs
    fill_runs = list(runs_dir.glob("uo2f2_fill_sweep_*"))

    # Also check for single fill sweep
    single_fill = runs_dir / "uo2f2_fill_sweep"
    if single_fill.exists():
        fill_runs.append(single_fill)

    if not fill_runs:
        print("No fill sweep runs found")
        return None

    # Load results from each run
    results_by_geometry = {}

    for run_dir in fill_runs:
        latest = find_latest_run(run_dir)
        if not latest:
            continue

        results = load_results(latest / "results.csv")
        if not results:
            continue

        # Generate geometry label from run name or first result
        if run_dir.name.startswith("uo2f2_fill_sweep_"):
            label = run_dir.name.replace("uo2f2_fill_sweep_", "")
        else:
            # Try to extract geometry info from results
            r = results[0]
            parts = []
            if 'pipe_size' in r:
                parts.append(f'{r["pipe_size"]}" pipe')
            if 'gap_cm' in r:
                parts.append(f'gap={r["gap_cm"]}cm')
            if 'rows' in r and 'cols' in r:
                parts.append(f'{r["rows"]}x{r["cols"]}')
            label = ", ".join(parts) if parts else run_dir.name

        results_by_geometry[label] = results

    if not results_by_geometry:
        print("No valid results found in fill sweep runs")
        return None

    # Set output path
    if output_path is None:
        plots_dir = exp_path / "summary_plots"
        plots_dir.mkdir(exist_ok=True)
        output_path = plots_dir / "fill_overlay.png"

    # Generate plot
    plot_fill_sweep_overlay(results_by_geometry, output_path, title)

    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python summary_plots.py <experiment_dir>")
        print("       python summary_plots.py <experiment_dir> --fill-overlay")
        sys.exit(1)

    if "--fill-overlay" in sys.argv:
        generate_fill_overlay_from_runs(sys.argv[1])
    else:
        generate_summary_plots(sys.argv[1])
