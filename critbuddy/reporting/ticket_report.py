#!/usr/bin/env python3
"""
Generate standardized ticket reports from experiment results.

Usage:
    from critbuddy.reporting.ticket_report import generate_ticket_report

    generate_ticket_report(
        experiment_dir="experiments/crit_requests/08_pipe_array_3d",
        ticket_id="CR-008",
        title="3D Pipe Array",
        requestor="Engineering",
    )
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


def load_results(results_csv: Path) -> List[Dict[str, Any]]:
    """Load results from CSV file."""
    if not results_csv.exists():
        return []

    with open(results_csv, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def find_latest_run(run_dir: Path) -> Optional[Path]:
    """Find the latest run directory (by timestamp or 'latest' symlink)."""
    if not run_dir.exists():
        return None

    latest_link = run_dir / "latest"
    if latest_link.exists():
        return latest_link

    # Find most recent timestamped directory
    dirs = [d for d in run_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
    if not dirs:
        return None
    return max(dirs, key=lambda d: d.name)


def format_table_row(row: Dict, columns: List[str]) -> str:
    """Format a result row as markdown table row."""
    values = []
    for col in columns:
        val = row.get(col, '')
        if col == 'keff':
            val = f"{float(val):.3f}" if val else ''
        elif col == 'keff_2sigma':
            val = f"{float(val):.3f}" if val else ''
        elif col == 'fill_fraction':
            val = f"{float(val)*100:.0f}%" if val else ''
        elif col == 'h_to_u':
            val = str(int(float(val))) if val else ''
        values.append(str(val))
    return "| " + " | ".join(values) + " |"


def determine_status(keff_2sigma: float) -> str:
    """Determine safety status from k-eff + 2sigma."""
    if keff_2sigma < 0.95:
        return "SAFE"
    elif keff_2sigma < 1.0:
        return "MARGINAL"
    else:
        return "CRITICAL"


def generate_ticket_report(
    experiment_dir: str,
    ticket_id: str,
    title: str,
    requestor: str = "Engineering",
    equipment_type: str = "",
    output_filename: str = "TICKET_SUMMARY.md",
) -> Path:
    """
    Generate a standardized ticket report from experiment results.

    Args:
        experiment_dir: Path to experiment directory
        ticket_id: YouTrack ticket ID (e.g., "CR-008")
        title: Report title (e.g., "3D Pipe Array")
        requestor: Who requested the analysis
        equipment_type: Type of equipment (auto-detected if not provided)
        output_filename: Output markdown filename

    Returns:
        Path to generated report
    """
    exp_path = Path(experiment_dir)
    runs_dir = exp_path / "runs"

    # Load results from each scenario (standard 3-config naming)
    uf6_run = find_latest_run(runs_dir / "uf6_dry")
    hu_run = find_latest_run(runs_dir / "uo2f2_hu_sweep")
    fill_run = find_latest_run(runs_dir / "uo2f2_fill_sweep")

    uf6_results = load_results(uf6_run / "results.csv") if uf6_run else []
    hu_results = load_results(hu_run / "results.csv") if hu_run else []
    fill_results = load_results(fill_run / "results.csv") if fill_run else []

    # Extract key values
    uf6_max_keff = max(float(r['keff_2sigma']) for r in uf6_results) if uf6_results else 0
    # For fill sweep at 100%, get max k-eff as "wet" reference
    fill_100_results = [r for r in fill_results if float(r.get('fill_fraction', 1.0)) >= 0.99]
    wet_max_keff = max(float(r['keff_2sigma']) for r in fill_100_results) if fill_100_results else 0

    # Find peak H/U
    peak_hu = 0
    if hu_results:
        peak_row = max(hu_results, key=lambda r: float(r['keff']))
        peak_hu = int(float(peak_row['h_to_u']))

    # Find critical threshold from fill sweep
    crit_fill = None
    safe_fill = None
    safe_keff = None

    if fill_results:
        sorted_fill = sorted(fill_results, key=lambda r: float(r['fill_fraction']), reverse=True)
        for r in sorted_fill:
            fill_pct = float(r['fill_fraction']) * 100
            k2s = float(r['keff_2sigma'])
            if k2s < 0.95 and safe_fill is None:
                safe_fill = fill_pct
                safe_keff = k2s
            if k2s >= 1.0 and crit_fill is None:
                crit_fill = fill_pct

        # Interpolate critical threshold
        for i in range(len(sorted_fill) - 1):
            k1 = float(sorted_fill[i]['keff_2sigma'])
            k2 = float(sorted_fill[i+1]['keff_2sigma'])
            f1 = float(sorted_fill[i]['fill_fraction']) * 100
            f2 = float(sorted_fill[i+1]['fill_fraction']) * 100
            if k1 >= 1.0 and k2 < 1.0:
                # Linear interpolation
                crit_fill = f2 + (f1 - f2) * (1.0 - k2) / (k1 - k2)
                break

    # Detect enrichment
    enrichment = 21  # default
    if uf6_results:
        enrichment = int(float(uf6_results[0].get('enrichment', 21)))

    # Detect template from config
    template_name = equipment_type or "unknown"
    config_files = list((exp_path / "_config").glob("*.yaml")) if (exp_path / "_config").exists() else []

    # Identify swept parameters
    swept_params = []
    if uf6_results and len(uf6_results) > 1:
        # Find columns with multiple unique values
        for col in uf6_results[0].keys():
            if col in ['case', 'solver', 'keff', 'std', 'keff_2sigma', 'status', 'execution_time']:
                continue
            unique_vals = set(r[col] for r in uf6_results)
            if len(unique_vals) > 1:
                swept_params.append(col)

    # Generate report
    now = datetime.now()

    report = f"""# Criticality Safety Analysis: {title}

**Ticket:** {ticket_id}
**Date:** {now.strftime('%Y-%m-%d')}
**Status:** ANALYSIS COMPLETE

---

## Request

| Field | Value |
|-------|-------|
| **Equipment** | {equipment_type or title} |
| **Template** | {template_name} |
| **Enrichment** | {enrichment}% |
| **Requestor** | {requestor} |

### Parameters Analyzed

| Parameter | Values |
|-----------|--------|
"""

    for param in swept_params[:3]:  # Top 3 swept params
        if uf6_results:
            vals = sorted(set(r[param] for r in uf6_results))
            report += f"| {param} | {', '.join(str(v) for v in vals)} |\n"

    # Geometry section
    geom_img = exp_path / "_validation" / "geometry.png"
    if geom_img.exists():
        report += f"""
---

## Configuration

### Geometry

![Geometry](_validation/geometry.png)

"""

    report += f"""### Environment

| Parameter | Value |
|-----------|-------|
| Environment | Humid air (100% RH @ 40°C) |
| Reflector | 30 cm humid air |
| Enrichment | {enrichment}% |

---

## Results Summary

### Finding

"""

    # Generate finding statement
    uf6_status = determine_status(uf6_max_keff)
    wet_status = determine_status(wet_max_keff)

    if uf6_status == "SAFE" and wet_status == "CRITICAL":
        finding = f"UF6 is safe by design. UO2F2 wet requires fill limit ≤{safe_fill:.0f}%." if safe_fill else "UF6 is safe by design. UO2F2 wet is critical at 100% fill."
    elif uf6_status == "SAFE" and wet_status == "SAFE":
        finding = "All scenarios are safe by design."
    else:
        finding = f"See detailed results below."

    report += f"> **{finding}**\n\n"

    # Safety status table
    report += """### Safety Status

| Scenario | Max k-eff | Status | Recommendation |
|----------|-----------|--------|----------------|
"""

    uf6_rec = "No controls required" if uf6_status == "SAFE" else "Fill limit required"
    wet_rec = "Fill limit required" if wet_status == "CRITICAL" else "No controls required"
    safe_rec = "Administrative limit" if safe_fill else "N/A"

    report += f"| UF6 Dry (100% fill) | {uf6_max_keff:.2f} | {uf6_status} | {uf6_rec} |\n"
    report += f"| UO2F2 Wet (100% fill) | {wet_max_keff:.2f} | {wet_status} | {wet_rec} |\n"
    if safe_fill and safe_keff:
        report += f"| UO2F2 Wet (≤{safe_fill:.0f}% fill) | {safe_keff:.2f} | SAFE | {safe_rec} |\n"

    # Critical threshold
    if crit_fill:
        # Find worst-case geometry from UF6 results
        worst_geom = "N/A"
        if uf6_results:
            worst_row = max(uf6_results, key=lambda r: float(r['keff']))
            geom_parts = []
            for p in swept_params[:2]:
                if p in worst_row:
                    geom_parts.append(f"{p}={worst_row[p]}")
            worst_geom = ", ".join(geom_parts) if geom_parts else "worst case"

        report += f"""
### Critical Threshold

| Material | Geometry | Critical Fill % |
|----------|----------|-----------------|
| UO2F2 Wet (H/U={peak_hu}) | {worst_geom} | ~{crit_fill:.0f}% |

"""

    # Detailed results tables
    report += """---

## Detailed Results

### 1. UF6 Dry (100% Fill)

"""

    if uf6_results:
        cols = swept_params[:2] + ['keff', 'keff_2sigma', 'status']
        report += "| " + " | ".join(cols) + " |\n"
        report += "|" + "|".join(["---"] * len(cols)) + "|\n"
        for row in uf6_results:
            report += format_table_row(row, cols) + "\n"

    # H/U sweep
    report += """
### 2. H/U Ratio Sweep

"""

    if hu_results:
        cols = ['h_to_u', 'keff', 'keff_2sigma', 'status']
        report += "| H/U | k-eff | k+2σ | Status |\n"
        report += "|-----|-------|------|--------|\n"
        for row in sorted(hu_results, key=lambda r: float(r['h_to_u'])):
            report += format_table_row(row, cols) + "\n"
        report += f"\n**Peak H/U:** {peak_hu}\n"

    # Fill sweep (combines worst-case geometry + peak H/U)
    report += """
### 3. Fill Fraction Sweep (Worst-Case Geometry + Peak H/U)

"""

    if fill_results:
        report += "| Fill % | k-eff | k+2σ | Status |\n"
        report += "|--------|-------|------|--------|\n"
        for row in sorted(fill_results, key=lambda r: float(r['fill_fraction']), reverse=True):
            report += format_table_row(row, ['fill_fraction', 'keff', 'keff_2sigma', 'status']) + "\n"

    # Plots section
    summary_plots = exp_path / "summary_plots"
    report += """
---

## Plots

"""

    if (summary_plots / "geometry_comparison.png").exists():
        report += "### Geometry Comparison\n![Geometry Comparison](summary_plots/geometry_comparison.png)\n\n"

    if (summary_plots / "fill_sweep.png").exists():
        report += "### Fill Fraction Sweep\n![Fill Sweep](summary_plots/fill_sweep.png)\n\n"

    if (summary_plots / "hu_sweep.png").exists():
        report += "### H/U Ratio Sweep\n![H/U Sweep](summary_plots/hu_sweep.png)\n\n"

    # Recommendations
    report += """---

## Recommendations

"""

    if uf6_status == "SAFE":
        report += f"1. **UF6 Operation:** No criticality controls required. Safe by design (k-eff = {uf6_max_keff:.2f}).\n\n"
    else:
        report += f"1. **UF6 Operation:** Fill limit required (max k-eff = {uf6_max_keff:.2f}).\n\n"

    if wet_status == "CRITICAL" and safe_fill:
        margin = crit_fill / safe_fill if crit_fill and safe_fill else 0
        report += f"2. **UO2F2 Wet Scenarios:** Administrative fill limit of ≤{safe_fill:.0f}% required.\n\n"
        report += f"3. **Safety Margin:** {margin:.2f}× margin to critical ({crit_fill:.0f}% critical / {safe_fill:.0f}% limit).\n\n"
    elif wet_status == "SAFE":
        report += "2. **UO2F2 Wet Scenarios:** No additional controls required. Safe by design.\n\n"

    # Config files
    report += """---

## Configuration Files

| File | Purpose |
|------|---------|
"""

    for cfg in sorted(config_files):
        purpose = {
            'uf6_dry': 'UF6 dry geometry sweep',
            'uo2f2_hu_sweep': 'H/U optimization at worst-case geometry',
            'uo2f2_fill_sweep': 'Fill sweep at worst-case + peak H/U',
        }.get(cfg.stem, cfg.stem)
        report += f"| `_config/{cfg.name}` | {purpose} |\n"

    # Run info
    report += """
---

## Run Info

| Scenario | Cases | Directory |
|----------|-------|-----------|
"""

    if uf6_run:
        report += f"| UF6 Dry | {len(uf6_results)} | `{uf6_run.relative_to(exp_path)}` |\n"
    if hu_run:
        report += f"| H/U Sweep | {len(hu_results)} | `{hu_run.relative_to(exp_path)}` |\n"
    if fill_run:
        report += f"| Fill Sweep | {len(fill_results)} | `{fill_run.relative_to(exp_path)}` |\n"

    total_cases = len(uf6_results) + len(hu_results) + len(fill_results)
    report += f"""
**Total:** {total_cases} cases
**Solver:** OpenMC v0.15.x with ENDF/B-VIII.0

---

*Generated by crit-buddy on {now.strftime('%Y-%m-%d %H:%M')}*
"""

    # Write report
    output_path = exp_path / output_filename
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"Generated: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python ticket_report.py <experiment_dir> <ticket_id> [title]")
        sys.exit(1)

    exp_dir = sys.argv[1]
    ticket_id = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else Path(exp_dir).name

    generate_ticket_report(exp_dir, ticket_id, title)
