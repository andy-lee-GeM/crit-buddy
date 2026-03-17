"""
Report generator for criticality experiment results.

Generates comprehensive reports with:
- Experiment summary
- Parameter configuration
- Results table
- Plots (embedded or linked)
- Safety conclusions

Also generates calculation reports following formal template structure:
- References
- Purpose and Experiment Setup
- Inputs
- Assumptions
- Methods
- Results
- Conclusions

Template-based reports use: docs/templates/cb-final-report-template.md
"""

from pathlib import Path
from typing import Optional, List, Dict, Union
from datetime import datetime
import pandas as pd
import shutil
import csv


# Project root for accessing templates
PROJECT_ROOT = Path(__file__).parent.parent.parent
TEMPLATE_PATH = PROJECT_ROOT / "docs" / "templates" / "cb-final-report-template.md"


def generate_report(
    run_dir: Path,
    experiment_yaml: Path,
    output_format: str = "markdown",
) -> Path:
    """
    Generate a comprehensive experiment report.

    Args:
        run_dir: Directory containing results.csv and plots/
        experiment_yaml: Path to the experiment YAML file
        output_format: "markdown" or "html"

    Returns:
        Path to generated report file
    """
    run_dir = Path(run_dir)
    experiment_yaml = Path(experiment_yaml)

    # Load results
    results_csv = run_dir / "results.csv"
    if not results_csv.exists():
        raise FileNotFoundError(f"Results not found: {results_csv}")

    df = pd.read_csv(results_csv)

    # Load experiment config
    import yaml
    with open(experiment_yaml) as f:
        config = yaml.safe_load(f)

    # Generate report content
    report = _generate_markdown_report(df, config, run_dir, experiment_yaml)

    # Write report
    report_path = run_dir / "REPORT.md"
    with open(report_path, "w") as f:
        f.write(report)

    return report_path


def _generate_markdown_report(
    df: pd.DataFrame,
    config: dict,
    run_dir: Path,
    experiment_yaml: Path,
) -> str:
    """Generate markdown report content."""

    # Extract info
    name = config.get("name", experiment_yaml.stem)
    model = config.get("model")
    problem = config.get("problem")
    definition_kind = "Model" if model else "Problem Template"
    definition_name = model or problem or "unknown"
    timestamp = run_dir.name

    # Identify swept and fixed parameters
    standard_cols = {"case", "solver", "keff", "std", "keff_2sigma", "status", "execution_time"}
    param_cols = [c for c in df.columns if c not in standard_cols]

    swept_params = {}
    fixed_params = {}
    for col in param_cols:
        unique_vals = df[col].unique()
        if len(unique_vals) > 1:
            swept_params[col] = sorted(unique_vals.tolist())
        else:
            fixed_params[col] = unique_vals[0]

    # Statistics
    n_cases = len(df)
    n_safe = len(df[df["status"] == "SAFE"])
    n_marginal = len(df[df["status"] == "MARGINAL"])
    n_critical = len(df[df["status"] == "CRITICAL"])

    keff_min = df["keff"].min()
    keff_max = df["keff"].max()
    keff_mean = df["keff"].mean()

    # Build report
    lines = []

    # Header
    lines.append(f"# Criticality Analysis Report")
    lines.append(f"")
    lines.append(f"**Experiment:** {name}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Run Directory:** `{run_dir}`")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Executive Summary
    lines.append(f"## Executive Summary")
    lines.append(f"")

    if n_critical == n_cases:
        lines.append(f"**Result: ALL CASES CRITICAL**")
        lines.append(f"")
        lines.append(f"All {n_cases} cases exceeded criticality (k-eff + 2σ ≥ 1.0). ")
        lines.append(f"No safe geometry exists within the analyzed parameter range under these conditions.")
    elif n_safe == n_cases:
        lines.append(f"**Result: ALL CASES SAFE**")
        lines.append(f"")
        lines.append(f"All {n_cases} cases are subcritical (k-eff + 2σ < 0.95).")
    else:
        lines.append(f"**Result: MIXED SAFETY STATUS**")
        lines.append(f"")
        lines.append(f"- SAFE: {n_safe} cases ({100*n_safe/n_cases:.1f}%)")
        lines.append(f"- MARGINAL: {n_marginal} cases ({100*n_marginal/n_cases:.1f}%)")
        lines.append(f"- CRITICAL: {n_critical} cases ({100*n_critical/n_cases:.1f}%)")

    lines.append(f"")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Cases | {n_cases} |")
    lines.append(f"| k-eff Range | {keff_min:.4f} - {keff_max:.4f} |")
    lines.append(f"| k-eff Mean | {keff_mean:.4f} |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Experiment Configuration
    lines.append(f"## Experiment Configuration")
    lines.append(f"")
    lines.append(f"**{definition_kind}:** `{definition_name}`")
    lines.append(f"")

    # Swept parameters
    lines.append(f"### Swept Parameters")
    lines.append(f"")
    if swept_params:
        lines.append(f"| Parameter | Values | Count |")
        lines.append(f"|-----------|--------|-------|")
        for param, values in swept_params.items():
            if len(values) <= 10:
                val_str = ", ".join(str(v) for v in values)
            else:
                val_str = f"{values[0]} ... {values[-1]}"
            lines.append(f"| `{param}` | {val_str} | {len(values)} |")
    else:
        lines.append(f"No parameters were swept (single case).")
    lines.append(f"")

    # Fixed parameters
    lines.append(f"### Fixed Parameters")
    lines.append(f"")
    if fixed_params:
        lines.append(f"| Parameter | Value |")
        lines.append(f"|-----------|-------|")
        for param, value in fixed_params.items():
            lines.append(f"| `{param}` | {value} |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Results Visualization
    lines.append(f"## Results Visualization")
    lines.append(f"")

    plots_dir = run_dir / "plots"
    if plots_dir.exists():
        plot_files = sorted(plots_dir.glob("*.png"))

        # Prioritize heatmaps
        heatmaps = [p for p in plot_files if "heatmap" in p.name]
        status_maps = [p for p in plot_files if "status" in p.name]
        line_plots = [p for p in plot_files if p not in heatmaps and p not in status_maps]

        if heatmaps:
            lines.append(f"### k-eff Heatmap")
            lines.append(f"")
            for plot in heatmaps:
                lines.append(f"![k-eff Heatmap](plots/{plot.name})")
            lines.append(f"")

        if status_maps:
            lines.append(f"### Safety Status Map")
            lines.append(f"")
            for plot in status_maps:
                lines.append(f"![Safety Status](plots/{plot.name})")
            lines.append(f"")

        if line_plots:
            lines.append(f"### Parameter Sweeps")
            lines.append(f"")
            for plot in line_plots:
                lines.append(f"![{plot.stem}](plots/{plot.name})")
                lines.append(f"")
    else:
        lines.append(f"No plots available.")

    lines.append(f"---")
    lines.append(f"")

    # Results Table
    lines.append(f"## Detailed Results")
    lines.append(f"")
    lines.append(f"<details>")
    lines.append(f"<summary>Click to expand full results table ({n_cases} cases)</summary>")
    lines.append(f"")

    # Create condensed table manually (no tabulate dependency)
    display_cols = ["case", "keff", "std", "status"] + list(swept_params.keys())
    table_df = df[display_cols].copy()

    # Create markdown table header
    lines.append("| " + " | ".join(display_cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(display_cols)) + " |")

    # Add rows
    for _, row in table_df.iterrows():
        row_vals = []
        for col in display_cols:
            val = row[col]
            if col == "keff" or col == "std":
                row_vals.append(f"{val:.5f}")
            else:
                row_vals.append(str(val))
        lines.append("| " + " | ".join(row_vals) + " |")
    lines.append(f"")
    lines.append(f"</details>")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Conservative Assumptions
    lines.append(f"## Analysis Assumptions")
    lines.append(f"")
    lines.append(f"This analysis uses **conservative (bounding)** assumptions:")
    lines.append(f"")

    # Check for common conservative parameters
    enrichment = fixed_params.get("enrichment", config.get("enrichment", "varied"))
    reflector = fixed_params.get("reflector_material", config.get("reflector_material", "unknown"))

    lines.append(f"| Assumption | Value | Conservative? |")
    lines.append(f"|------------|-------|---------------|")
    if isinstance(enrichment, (int, float)):
        lines.append(f"| Enrichment | {enrichment}% | {'✓' if enrichment >= 20 else '?'} |")
    lines.append(f"| Reflector | {reflector} | {'✓ Full reflection' if reflector == 'water' else '?'} |")
    lines.append(f"| Fill Level | 100% | ✓ |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Conclusions
    lines.append(f"## Conclusions")
    lines.append(f"")

    if n_critical == n_cases:
        lines.append(f"At the analyzed conditions, **no safe geometry exists** within the parameter range:")
        lines.append(f"")
        for param, values in swept_params.items():
            lines.append(f"- {param}: {min(values)} - {max(values)}")
        lines.append(f"")
        lines.append(f"**Recommendations:**")
        lines.append(f"- Consider lower enrichment levels")
        lines.append(f"- Use favorable geometry (pipes instead of open vessels)")
        lines.append(f"- Implement administrative controls (mass limits)")
    elif n_safe == n_cases:
        lines.append(f"All analyzed geometries are **subcritical** under conservative assumptions.")
        lines.append(f"")
        lines.append(f"The analyzed equipment can be operated safely within the parameter ranges.")
    else:
        lines.append(f"A **safe operating envelope** exists within the analyzed parameter range.")
        lines.append(f"")
        lines.append(f"Refer to the heatmap and status plots for specific safe/unsafe boundaries.")

    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*Report generated by Crit-Buddy*")

    return "\n".join(lines)


def generate_calculation_report(
    run_dirs: Dict[str, Union[str, Path]],
    output_path: Union[str, Path],
    experiment_name: str = "Cascade Cylinder Array",
    calc_number: str = "[To Be Assigned]",
) -> Path:
    """
    Generate a formal calculation report following the Word template structure.

    This creates a comprehensive markdown report suitable for regulatory
    documentation, following the structure:
    1. References
    2. Purpose and Experiment Setup
    3. Inputs
    4. Assumptions
    5. Methods
    6. Results
    7. Conclusions
    8. Attachments

    Args:
        run_dirs: Dict mapping condition names to run directories
                  e.g., {"optimal": "/path/to/0.5_run", "flooded": "/path/to/1.0_run"}
        output_path: Path for output markdown file
        experiment_name: Name for report title
        calc_number: Calculation tracking number

    Returns:
        Path to generated markdown file
    """
    output_path = Path(output_path)

    # Load all results
    results = {}
    for condition, run_dir in run_dirs.items():
        run_dir = Path(run_dir)
        csv_path = run_dir / "results.csv"
        if csv_path.exists():
            results[condition] = {
                "df": pd.read_csv(csv_path),
                "path": run_dir,
            }
        else:
            raise FileNotFoundError(f"Results not found: {csv_path}")

    lines = []

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    lines.append("# Criticality Safety Analysis")
    lines.append(f"## {experiment_name} Configuration")
    lines.append("")
    lines.append(f"**Calculation Number:** {calc_number}")
    lines.append("**Revision:** 0")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("| Role | Name | Date |")
    lines.append("|------|------|------|")
    lines.append("| Prepared by | | |")
    lines.append("| Reviewed by | | |")
    lines.append("| Approved by | | |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================================================
    # SECTION 1: REFERENCES
    # =========================================================================
    lines.append("## 1. References")
    lines.append("")
    lines.append("1. ANSI/ANS-8.1-2014, \"Nuclear Criticality Safety in Operations with Fissionable Materials Outside Reactors\"")
    lines.append("2. 10 CFR 70.24, \"Criticality Accident Requirements\"")
    lines.append("3. NUREG/CR-6698, \"Guide for Validation of Nuclear Criticality Safety Calculational Methodology\"")
    lines.append("4. OpenMC Monte Carlo Code (open-source particle transport)")
    lines.append("5. ENDF/B-VIII.0 Nuclear Data Library")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================================================
    # SECTION 2: PURPOSE
    # =========================================================================
    lines.append("## 2. Purpose")
    lines.append("")

    # Get array dimensions from data
    primary_df = list(results.values())[0]["df"]
    rows = int(primary_df["rows"].iloc[0]) if "rows" in primary_df.columns else "?"
    cols = int(primary_df["cols"].iloc[0]) if "cols" in primary_df.columns else "?"
    layers = int(primary_df["layers"].iloc[0]) if "layers" in primary_df.columns else "?"
    total_cyl = rows * cols * layers if all(isinstance(x, int) for x in [rows, cols, layers]) else "?"

    # Get enrichment and gap ranges for narrative
    standard_cols = {"case", "solver", "keff", "std", "keff_2sigma", "status", "execution_time"}
    param_cols = [c for c in primary_df.columns if c not in standard_cols]
    swept_params = {}
    fixed_params = {}
    for col in param_cols:
        unique_vals = primary_df[col].unique()
        if len(unique_vals) > 1:
            swept_params[col] = sorted(unique_vals.tolist())
        else:
            fixed_params[col] = unique_vals[0]

    enr_range = swept_params.get("enrichment", [])
    gap_range = swept_params.get("gap_xy_cm", [])
    enr_str = f"{min(enr_range)}% to {max(enr_range)}%" if enr_range else "various"
    gap_str = f"{min(gap_range)} cm to {max(gap_range)} cm" if gap_range else "various"

    lines.append(f"This analysis determines the minimum safe gap distance between cylinders in a {rows}×{cols}×{layers} cascade array configuration ({total_cyl} total cylinders). The study sweeps uranium enrichment from {enr_str} and horizontal gap spacing from {gap_str} to identify safe operating boundaries for storage and processing operations.")
    lines.append("")
    lines.append(f"The analysis addresses a key criticality safety question: at what cylinder spacing does a cascade array become subcritical for each enrichment level? Results from this parametric study provide the technical basis for administrative controls on cylinder placement and spacing requirements.")
    lines.append("")
    lines.append(f"Two water moderation conditions are evaluated: optimal moderation (0.5 g/cc, representing mist or partial flooding) and fully flooded (1.0 g/cc). The optimal moderation case is typically the limiting condition for multi-unit arrays because intermediate water densities can produce higher reactivity than full flooding due to the balance between moderation benefit and neutron absorption.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================================================
    # SECTION 3: INPUTS
    # =========================================================================
    lines.append("## 3. Inputs")
    lines.append("")

    # Copy geometry image to plots directory if it exists
    validation_dir = output_path.parent / "_validation"
    geometry_img = validation_dir / "geometry.png"
    if geometry_img.exists():
        import shutil
        plots_dir = output_path.parent / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(str(geometry_img), str(plots_dir / "geometry.png"))
        lines.append("### 3.1 Geometry Visualization")
        lines.append("")
        lines.append("![Geometry Cross-Section](plots/geometry.png)")
        lines.append("")
        lines.append("*Figure: XY cross-section showing cylinder array layout with UF6 (yellow), steel walls (gray), and water (blue).*")
        lines.append("")

    lines.append("### 3.2 Array Configuration")
    lines.append("")
    lines.append("| Parameter | Value | Units |")
    lines.append("|-----------|-------|-------|")
    lines.append(f"| Rows (X direction) | {rows} | - |")
    lines.append(f"| Columns (Y direction) | {cols} | - |")
    lines.append(f"| Layers (Z direction) | {layers} | - |")
    lines.append(f"| Total cylinders | {total_cyl} | - |")
    lines.append("")

    # Cylinder geometry
    radius = primary_df["radius_cm"].iloc[0] if "radius_cm" in primary_df.columns else "?"
    wall_t = primary_df["wall_thickness_cm"].iloc[0] if "wall_thickness_cm" in primary_df.columns else "?"
    height = primary_df["height_cm"].iloc[0] if "height_cm" in primary_df.columns else "?"

    outer_r = radius + wall_t if all(isinstance(x, (int, float)) for x in [radius, wall_t]) else "?"
    total_h = height + 2 * wall_t if all(isinstance(x, (int, float)) for x in [height, wall_t]) else "?"

    lines.append("### 3.3 Cylinder Geometry")
    lines.append("")
    lines.append("| Parameter | Value | Units |")
    lines.append("|-----------|-------|-------|")
    lines.append(f"| Inner radius | {radius} | cm |")
    lines.append(f"| Wall thickness | {wall_t} | cm |")
    lines.append(f"| Outer radius | {outer_r:.4f} | cm |" if isinstance(outer_r, float) else f"| Outer radius | {outer_r} | cm |")
    lines.append(f"| UF6 height | {height} | cm |")
    lines.append(f"| Total height (with caps) | {total_h:.2f} | cm |" if isinstance(total_h, float) else f"| Total height | {total_h} | cm |")
    lines.append(f"| Inner diameter | {2*radius:.2f} | cm |" if isinstance(radius, (int, float)) else f"| Inner diameter | ? | cm |")
    lines.append(f"| Outer diameter | {2*outer_r:.2f} | cm |" if isinstance(outer_r, float) else f"| Outer diameter | ? | cm |")
    lines.append("")

    # Materials
    uf6_density = primary_df["uf6_density"].iloc[0] if "uf6_density" in primary_df.columns else 5.09
    wall_mat = primary_df["wall_material"].iloc[0] if "wall_material" in primary_df.columns else "steel"

    lines.append("### 3.4 Materials")
    lines.append("")
    lines.append("| Material | Composition | Density (g/cc) |")
    lines.append("|----------|-------------|----------------|")
    lines.append(f"| UF6 | Solid uranium hexafluoride | {uf6_density} |")
    lines.append(f"| Wall | {wall_mat.title()} | 8.0 |")
    lines.append("| Water | H2O (moderator and reflector) | Variable |")
    lines.append("")
    lines.append("*Note: Water serves as both moderator (between cylinders) and reflector (surrounding the array).*")
    lines.append("")

    # Parameter ranges
    lines.append("### 3.5 Parameter Ranges Analyzed")
    lines.append("")
    lines.append("| Parameter | Values | Units |")
    lines.append("|-----------|--------|-------|")
    if "enrichment" in swept_params:
        vals = ", ".join(str(v) for v in swept_params["enrichment"])
        lines.append(f"| Enrichment | {vals} | wt% U-235 |")
    if "gap_xy_cm" in swept_params:
        vals = ", ".join(str(v) for v in swept_params["gap_xy_cm"])
        lines.append(f"| Horizontal gap (XY) | {vals} | cm |")
    if "gap_z_cm" in fixed_params:
        lines.append(f"| Vertical gap (Z) | {fixed_params['gap_z_cm']} (fixed) | cm |")

    # Water densities from different conditions
    water_densities = []
    for cond, data in results.items():
        if "water_density" in data["df"].columns:
            wd = data["df"]["water_density"].iloc[0]
            water_densities.append(f"{wd}")
    if water_densities:
        lines.append(f"| Water density (moderator/reflector) | {', '.join(water_densities)} | g/cc |")

    if "water_thickness_cm" in fixed_params:
        lines.append(f"| Water thickness (reflector) | {fixed_params['water_thickness_cm']} | cm |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================================================
    # SECTION 4: ASSUMPTIONS
    # =========================================================================
    lines.append("## 4. Assumptions")
    lines.append("")

    lines.append("### 4.1 Optimal Moderation Analysis")
    lines.append("")
    lines.append("For multi-unit arrays, the most reactive water density is NOT fully flooded (1.0 g/cc).")
    lines.append("Instead, intermediate densities (\"optimal moderation\") can produce higher k-eff values due to the balance between:")
    lines.append("")
    lines.append("- **Moderation benefit**: Water thermalizes neutrons, increasing fission probability")
    lines.append("- **Absorption penalty**: More water = more neutron absorption between units")
    lines.append("")
    lines.append("A preliminary moderation sweep identified ~0.5 g/cc as peak reactivity, representing conditions such as:")
    lines.append("- Water mist/fog accumulation")
    lines.append("- Partial flooding scenarios")
    lines.append("- Fire suppression spray conditions")
    lines.append("")
    lines.append("**Conservative approach**: Array analyses include 0.5 g/cc water to bound the worst-case moderation scenario.")
    lines.append("")

    lines.append("### 4.2 Conservative Assumptions Summary")
    lines.append("")
    lines.append("| Assumption | Value Used | Justification |")
    lines.append("|------------|------------|---------------|")
    lines.append("| UF6 form | Pure solid | Bounds actual chemistry (complexes reduce reactivity) |")
    lines.append(f"| UF6 density | {uf6_density} g/cc | Maximum solid density |")
    lines.append("| Fill level | 100% | Assumes fully loaded cylinders |")
    lines.append("| Temperature | Room temperature | Most reactive condition |")
    if "enrichment" in swept_params:
        max_enr = max(swept_params["enrichment"])
        lines.append(f"| Enrichment | Up to {max_enr}% | Bounds HALEU operations |")
    lines.append("| Water density | 0.5 g/cc | Peak reactivity from moderation sweep |")
    if "water_thickness_cm" in fixed_params:
        lines.append(f"| Reflection | {fixed_params['water_thickness_cm']} cm water | Full reflection on all sides |")
    lines.append(f"| Wall material | {wall_mat.title()} | Realistic for process equipment |")
    lines.append("")

    lines.append("### 4.3 Non-Conservative Aspects")
    lines.append("")
    lines.append("| Aspect | Impact |")
    lines.append("|--------|--------|")
    lines.append("| Steel walls | Slight neutron absorption (actual k-eff would be slightly lower) |")
    lines.append("| Uniform enrichment | Real operations may have mixed enrichments |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================================================
    # SECTION 5: METHODS
    # =========================================================================
    lines.append("## 5. Analytical Methods and Computations")
    lines.append("")

    lines.append("### 5.1 Monte Carlo Code")
    lines.append("")
    lines.append("- **Code**: OpenMC (open-source Monte Carlo particle transport)")
    lines.append("- **Nuclear data**: ENDF/B-VIII.0 continuous-energy cross sections")
    lines.append("- **Thermal scattering**: S(α,β) treatment for hydrogen in water")
    lines.append("")

    lines.append("### 5.2 Simulation Parameters")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append("| Particles per batch | 10,000 |")
    lines.append("| Total batches | 150 |")
    lines.append("| Inactive batches | 50 |")
    lines.append("| Active batches | 100 |")
    lines.append("| Total histories | 1,000,000 |")
    lines.append("")

    lines.append("### 5.3 Geometry Model")
    lines.append("")
    lines.append(f"- **3D explicit geometry**: Each of {total_cyl} cylinders modeled individually")
    lines.append("- **Cylinder components**: UF6 core, steel wall, top/bottom steel caps")
    lines.append("- **Water**: Surrounds all cylinders and fills gaps")
    lines.append("- **Boundary conditions**: Vacuum at outer boundaries")
    lines.append("")

    lines.append("### 5.4 Statistical Uncertainty")
    lines.append("")
    lines.append("- Expected 1σ uncertainty: ~80-100 pcm")
    lines.append("- **Safety margin**: k-eff + 2σ used for all safety determinations")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================================================
    # SECTION 6: RESULTS
    # =========================================================================
    lines.append("## 6. Results")
    lines.append("")

    # Generate and save plots for each condition
    from critbuddy.reporting.plots import plot_keff_vs_gap_by_enrichment, plot_heatmap

    plots_dir = output_path.parent / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    section_num = 1
    for cond_name, data in results.items():
        df = data["df"]
        water_dens = df["water_density"].iloc[0] if "water_density" in df.columns else "?"

        # Determine section title and explanation based on water density
        if water_dens <= 0.5:
            section_title = "Worst-Case Moderation"
            explanation = (
                "This scenario uses 0.5 g/cc water density, which represents the worst-case "
                "(most reactive) moderation condition for multi-unit arrays. This bounds scenarios "
                "such as water mist accumulation, fog, partial flooding, or fire suppression spray. "
                "At this density, neutron moderation between units is optimized while absorption "
                "losses are minimized, producing the highest k-effective values."
            )
        else:
            section_title = "Flooded"
            explanation = (
                "This scenario uses 1.0 g/cc water density, representing fully flooded conditions. "
                "While intuitively one might expect full flooding to be the worst case, the additional "
                "water actually absorbs more neutrons traveling between units, resulting in lower "
                "k-effective values compared to the worst-case moderation scenario."
            )

        lines.append(f"### 6.{section_num} {section_title} ({water_dens} g/cc)")
        section_num += 1
        lines.append("")
        lines.append(explanation)
        lines.append("")

        # Create pivot table if we have enrichment and gap
        if "enrichment" in df.columns and "gap_xy_cm" in df.columns:
            pivot = df.pivot_table(
                values="keff",
                index="enrichment",
                columns="gap_xy_cm",
                aggfunc="first"
            )

            # k-eff table (just numbers, no status)
            gap_cols = sorted(df["gap_xy_cm"].unique())
            lines.append("**k-effective vs Enrichment and Gap**")
            lines.append("")
            lines.append("| Enrichment | " + " | ".join(f"{g} cm" for g in gap_cols) + " |")
            lines.append("|------------|" + "|".join(["------"] * len(gap_cols)) + "|")

            for enr in sorted(df["enrichment"].unique()):
                row_vals = [f"{enr}%"]
                for gap in gap_cols:
                    keff = pivot.loc[enr, gap]
                    row_vals.append(f"{keff:.4f}")
                lines.append("| " + " | ".join(row_vals) + " |")
            lines.append("")

        # Generate plots for this condition
        csv_path = data["path"] / "results.csv"
        cond_suffix = cond_name.replace(" ", "_").lower()

        # Line plot
        line_plot_path = plots_dir / f"keff_vs_gap_{cond_suffix}.png"
        plot_keff_vs_gap_by_enrichment(csv_path, line_plot_path)
        lines.append(f"![k-eff vs Gap - {section_title}](plots/keff_vs_gap_{cond_suffix}.png)")
        lines.append("")

        # Heatmap
        heatmap_paths = plot_heatmap(csv_path, plots_dir)
        if heatmap_paths:
            # Rename heatmap to include condition
            import shutil
            for hp in heatmap_paths:
                if "heatmap" in hp.name:
                    new_name = hp.name.replace("heatmap_", f"heatmap_{cond_suffix}_")
                    new_path = plots_dir / new_name
                    shutil.move(str(hp), str(new_path))
                    lines.append(f"![Heatmap - {section_title}](plots/{new_name})")
                    lines.append("")
                    break

    lines.append("---")
    lines.append("")

    # =========================================================================
    # SECTION 7: CONCLUSIONS
    # =========================================================================
    lines.append("## 7. Conclusions")
    lines.append("")

    lines.append("### Minimum Safe Gap by Enrichment")
    lines.append("")
    lines.append("Under conservative (bounding) conditions with optimal moderation (0.5 g/cc water):")
    lines.append("")

    # Use the condition with critical cases (typically optimal moderation)
    limiting_df = None
    limiting_cond = None
    for cond_name, data in results.items():
        df = data["df"]
        n_crit = len(df[df["status"] == "CRITICAL"])
        if n_crit > 0 or limiting_df is None:
            limiting_df = df
            limiting_cond = cond_name

    lines.append("| Enrichment | Minimum Safe Gap | k-eff at Min Gap | Safety Status |")
    lines.append("|------------|------------------|------------------|---------------|")

    if "enrichment" in limiting_df.columns and "gap_xy_cm" in limiting_df.columns:
        for enr in sorted(limiting_df["enrichment"].unique()):
            enr_data = limiting_df[limiting_df["enrichment"] == enr]
            safe_data = enr_data[enr_data["status"] == "SAFE"]

            if len(safe_data) > 0:
                min_gap_row = safe_data.loc[safe_data["gap_xy_cm"].idxmin()]
                min_gap = min_gap_row["gap_xy_cm"]
                keff = min_gap_row["keff"]
                status = "SAFE"
            else:
                max_gap = enr_data["gap_xy_cm"].max()
                min_gap = f"> {max_gap}"
                min_gap_row = enr_data.loc[enr_data["keff"].idxmin()]
                keff = min_gap_row["keff"]
                status = "CRITICAL at all gaps"

            lines.append(f"| **{enr}%** | **{min_gap} cm** | {keff:.4f} | {status} |")
    lines.append("")
    lines.append("*Note: \"Minimum Safe Gap\" is the smallest analyzed gap where k-eff + 2σ < 0.95*")
    lines.append("")

    # Key findings as narrative
    lines.append("### Key Findings")
    lines.append("")

    if len(results) >= 2:
        lines.append("The optimal moderation condition (0.5 g/cc water density) produces higher k-effective values than fully flooded conditions, making it the limiting case for safety analysis. This represents scenarios such as water mist accumulation or fire suppression spray.")
        lines.append("")

    if "enrichment" in limiting_df.columns and "gap_xy_cm" in limiting_df.columns:
        min_enr = limiting_df["enrichment"].min()
        max_gap = limiting_df["gap_xy_cm"].max()
        max_enr = limiting_df["enrichment"].max()

        # Check LEU behavior
        low_enr_data = limiting_df[limiting_df["enrichment"] == min_enr]
        if all(low_enr_data["status"] == "SAFE"):
            lines.append(f"At {min_enr}% enrichment (LEU), all analyzed gap distances are safe, with no spacing restrictions required within the analyzed range.")
            lines.append("")

        # Check max gap behavior
        max_gap_data = limiting_df[limiting_df["gap_xy_cm"] == max_gap]
        if all(max_gap_data["status"] == "SAFE"):
            lines.append(f"A gap distance of {max_gap} cm provides adequate spacing for subcriticality across all enrichment levels up to {max_enr}%.")
            lines.append("")

    lines.append("---")
    lines.append("")

    # =========================================================================
    # SECTION 8: ATTACHMENTS
    # =========================================================================
    lines.append("## 8. Attachments")
    lines.append("")
    lines.append("1. **Attachment A**: Geometry validation plots (XY, XZ cross-sections)")
    lines.append("2. **Attachment B**: Full results CSV files")
    lines.append("3. **Attachment C**: Heatmap visualizations")
    lines.append("4. **Attachment D**: Input YAML configuration files")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by Crit-Buddy*")

    # Write report
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def generate_template_report(
    experiment_dir: Union[str, Path],
    ticket_id: str,
    title: Optional[str] = None,
) -> Path:
    """
    Generate a report using the standard template (docs/templates/cb-final-report-template.md).

    This function collects results from all runs in an experiment directory and
    fills in the template placeholders.

    Args:
        experiment_dir: Path to experiment directory (e.g., experiments/crit_requests/CB-10)
        ticket_id: Ticket ID (e.g., "CB-10")
        title: Report title (default: derived from directory name)

    Returns:
        Path to generated report file (results/REPORT.md)
    """
    experiment_dir = Path(experiment_dir)
    runs_dir = experiment_dir / "runs"
    results_dir = experiment_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load template
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE_PATH}")
    template = TEMPLATE_PATH.read_text()

    # Collect results from all runs
    uf6_results = _load_latest_results(runs_dir / "uf6_dry")
    hu_results = _load_latest_results(runs_dir / "uo2f2_hu_sweep")

    # Collect fill sweep results (may be in uo2f2_fill_sweeps/ or uo2f2_fill_sweep/)
    fill_results = []
    fill_sweeps_dir = runs_dir / "uo2f2_fill_sweeps"
    single_fill_dir = runs_dir / "uo2f2_fill_sweep"

    if fill_sweeps_dir.exists():
        # Multiple fill sweep cases
        for case_dir in sorted(fill_sweeps_dir.iterdir()):
            if case_dir.is_dir():
                case_results = _load_latest_results(case_dir)
                if case_results:
                    fill_results.extend(case_results)
    elif single_fill_dir.exists():
        fill_results = _load_latest_results(single_fill_dir)

    # Extract key metrics
    uf6_max_keff = max((float(r['keff_2sigma']) for r in uf6_results), default=0)
    uf6_max_row = max(uf6_results, key=lambda r: float(r['keff'])) if uf6_results else {}

    # Find peak H/U
    peak_hu = 0
    if hu_results:
        peak_row = max(hu_results, key=lambda r: float(r['keff']))
        peak_hu = int(float(peak_row.get('h_to_u', 0)))

    # Find critical threshold from fill results
    critical_threshold = "N/A"
    if fill_results:
        sorted_fill = sorted(fill_results, key=lambda r: float(r.get('fill_fraction', 0)))
        for i in range(len(sorted_fill) - 1):
            k1 = float(sorted_fill[i]['keff_2sigma'])
            k2 = float(sorted_fill[i + 1]['keff_2sigma'])
            f1 = float(sorted_fill[i]['fill_fraction']) * 100
            f2 = float(sorted_fill[i + 1]['fill_fraction']) * 100
            if k1 < 0.95 <= k2:
                # Linear interpolation
                crit = f1 + (f2 - f1) * (0.95 - k1) / (k2 - k1)
                critical_threshold = f"~{crit:.0f}%"
                break

    # Build geometry table
    geometry_table = ""
    if uf6_results:
        r = uf6_results[0]
        for key in ['rows', 'cols', 'layers', 'radius_cm', 'height_cm', 'pipe_size',
                    'length_cm', 'gap_cm', 'gap_horizontal_cm', 'gap_vertical_cm']:
            if key in r:
                geometry_table += f"| {key} | {r[key]} |\n"

    # Build UF6 results table
    uf6_table = _format_results_table(uf6_results, ['keff', 'keff_2sigma', 'status'])

    # Build H/U results table
    hu_table = _format_results_table(hu_results, ['h_to_u', 'keff', 'keff_2sigma', 'status'])

    # Build fill results table
    fill_table = _format_results_table(fill_results, ['fill_fraction', 'keff', 'keff_2sigma', 'status'])

    # Extract other values
    enrichment = uf6_results[0].get('enrichment', '?') if uf6_results else '?'
    fissile_density = uf6_results[0].get('fissile_density', '5.09') if uf6_results else '5.09'

    # Worst-case geometry description
    worst_geom = []
    for key in ['rows', 'cols', 'pipe_size', 'gap_cm', 'gap_horizontal_cm']:
        if key in uf6_max_row:
            worst_geom.append(f"{key}={uf6_max_row[key]}")
    worst_case_geometry = ", ".join(worst_geom) if worst_geom else "See results table"

    # UO2F2 max k-eff (from fill results at 100%)
    uo2f2_max = 0
    for r in fill_results:
        if float(r.get('fill_fraction', 0)) >= 0.99:
            k2s = float(r['keff_2sigma'])
            if k2s > uo2f2_max:
                uo2f2_max = k2s

    # Status determination
    uf6_status = "SAFE" if uf6_max_keff < 0.95 else ("MARGINAL" if uf6_max_keff < 1.0 else "CRITICAL")
    uo2f2_status = "SAFE" if uo2f2_max < 0.95 else ("MARGINAL" if uo2f2_max < 1.0 else "CRITICAL")

    # Takeaways
    takeaways = []
    if uf6_status == "SAFE":
        takeaways.append(f"- UF6 dry scenario is **subcritical** (k+2σ = {uf6_max_keff:.3f})")
    if critical_threshold != "N/A":
        takeaways.append(f"- UO2F2 wet critical threshold: **{critical_threshold} fill**")
    takeaways_str = "\n".join(takeaways) if takeaways else "See detailed results above."

    # Additional plots (list any found)
    plots_dir = experiment_dir / "summary_plots"
    additional_plots = ""
    if plots_dir.exists():
        for plot in sorted(plots_dir.glob("*.png")):
            if plot.name not in ['geometry.png', 'keff_vs_fill_fraction.png', 'keff_vs_h_to_u.png']:
                additional_plots += f"\n### {plot.stem.replace('_', ' ').title()}\n\n![{plot.stem}](plots/{plot.name})\n"

    # Total cases
    total_cases = len(uf6_results) + len(hu_results) + len(fill_results)

    # Fill template
    report = template.format(
        TICKET_ID=ticket_id,
        TITLE=title or experiment_dir.name,
        DATE=datetime.now().strftime('%Y-%m-%d'),
        DESCRIPTION=f"Criticality safety analysis for {ticket_id}",
        OBJECTIVE="Determine safe operating envelope and critical thresholds",
        GEOMETRY_SUMMARY=worst_case_geometry,
        GEOMETRY_TABLE=geometry_table,
        FISSILE_DENSITY=fissile_density,
        ENRICHMENT=enrichment,
        WORST_CASE_GEOMETRY=worst_case_geometry,
        UF6_RESULTS_TABLE=uf6_table,
        PEAK_HU=peak_hu,
        HU_RESULTS_TABLE=hu_table,
        CRITICAL_THRESHOLD=critical_threshold.replace("~", "").replace("%", ""),
        FILL_RESULTS_TABLE=fill_table,
        UF6_KEFF_MAX=f"{uf6_max_keff:.4f}",
        UF6_K2SIGMA=f"{uf6_max_keff:.4f}",
        UF6_STATUS=uf6_status,
        UO2F2_KEFF_MAX=f"{uo2f2_max:.4f}",
        UO2F2_K2SIGMA=f"{uo2f2_max:.4f}",
        UO2F2_STATUS=uo2f2_status,
        TAKEAWAYS=takeaways_str,
        ADDITIONAL_PLOTS=additional_plots,
        TOTAL_CASES=total_cases,
    )

    # Write report
    output_path = results_dir / "REPORT.md"
    output_path.write_text(report)

    print(f"Generated: {output_path}")
    return output_path


def _load_latest_results(run_dir: Path) -> List[Dict]:
    """Load results from the latest run in a directory."""
    if not run_dir.exists():
        return []

    # Find latest
    latest_link = run_dir / "latest"
    if latest_link.exists():
        latest = latest_link
    else:
        dirs = [d for d in run_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
        if not dirs:
            return []
        latest = max(dirs, key=lambda d: d.name)

    results_csv = latest / "results.csv"
    if not results_csv.exists():
        return []

    with open(results_csv, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def _format_results_table(results: List[Dict], display_cols: List[str]) -> str:
    """Format results as markdown table."""
    if not results:
        return "No results available."

    # Get all columns
    all_cols = list(results[0].keys())
    cols = [c for c in display_cols if c in all_cols]

    if not cols:
        return "No matching columns."

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")

    for r in results[:20]:  # Limit to 20 rows
        row_vals = []
        for col in cols:
            val = r.get(col, '')
            if col in ['keff', 'keff_2sigma', 'std']:
                try:
                    row_vals.append(f"{float(val):.4f}")
                except ValueError:
                    row_vals.append(str(val))
            elif col == 'fill_fraction':
                try:
                    row_vals.append(f"{float(val)*100:.0f}%")
                except ValueError:
                    row_vals.append(str(val))
            else:
                row_vals.append(str(val))
        lines.append("| " + " | ".join(row_vals) + " |")

    if len(results) > 20:
        lines.append(f"\n*... and {len(results) - 20} more rows (see all_results.csv)*")

    return "\n".join(lines)
