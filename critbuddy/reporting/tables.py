"""
Table generation for results reporting.

Generates formatted tables for console output and markdown.
"""

from typing import Optional
import pandas as pd
import numpy as np

from .data import StudyResults


def results_table(results: StudyResults, format: str = "console") -> str:
    """
    Generate results table showing all cases.

    Args:
        results: StudyResults object
        format: "console" or "markdown"

    Returns:
        Formatted table string
    """
    df = results.data.copy()

    # Build display columns: swept params + solver + keff + std + status
    display_cols = results.swept_params + ["solver", "keff", "std", "keff_2sigma", "status"]

    # Filter to existing columns
    display_cols = [c for c in display_cols if c in df.columns]

    # Sort by swept parameters then solver
    sort_cols = results.swept_params + ["solver"] if results.swept_params else ["case", "solver"]
    sort_cols = [c for c in sort_cols if c in df.columns]
    df = df.sort_values(sort_cols)

    # Select and format
    table_df = df[display_cols].copy()

    # Round numeric columns
    for col in ["keff", "std", "keff_2sigma"]:
        if col in table_df.columns:
            table_df[col] = table_df[col].apply(lambda x: f"{x:.5f}" if pd.notna(x) else "---")

    if format == "markdown":
        return table_df.to_markdown(index=False)
    else:
        return table_df.to_string(index=False)


def comparison_table(results: StudyResults, format: str = "console", sigma: float = 2.0) -> str:
    """
    Generate solver comparison table.

    Args:
        results: StudyResults object
        format: "console" or "markdown"
        sigma: Number of combined sigmas for agreement threshold

    Returns:
        Formatted table string
    """
    if not results.has_multiple_solvers:
        return "Comparison requires multiple solvers"

    comp_df = results.get_comparison_data()

    # Build output rows
    rows = []
    for _, row in comp_df.iterrows():
        r = {}

        # Add swept parameters
        for param in results.swept_params:
            val = row[param]
            if isinstance(val, float):
                r[param] = f"{val:.4g}"
            else:
                r[param] = str(val)

        # Add solver k-eff values
        for solver in results.solvers:
            keff = row[f"{solver}_keff"]
            std = row[f"{solver}_std"]
            r[f"{solver}"] = f"{keff:.5f} +/- {std:.5f}"

        # Add delta if available
        if "delta_keff" in row:
            r["Δk"] = f"{row['delta_keff']:+.5f}"
            r["Δk (pcm)"] = f"{row['delta_pcm']:+.1f}"

            # Check agreement
            combined_std = np.sqrt(
                row.get("openmc_std", 0)**2 + row.get("mcnp_std", 0)**2
            )
            agrees = abs(row["delta_keff"]) < sigma * combined_std
            r["Agree"] = "✓" if agrees else "✗"

        rows.append(r)

    table_df = pd.DataFrame(rows)

    if format == "markdown":
        return table_df.to_markdown(index=False)
    else:
        return table_df.to_string(index=False)


def summary_table(results: StudyResults, format: str = "console") -> str:
    """
    Generate summary statistics table.

    Args:
        results: StudyResults object
        format: "console" or "markdown"

    Returns:
        Formatted summary string
    """
    stats = results.summary_stats()

    lines = []
    lines.append("STUDY SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Cases:           {stats['n_cases']}")
    lines.append(f"Solvers:         {', '.join(stats['solvers'])}")

    if stats['swept_params']:
        lines.append(f"Swept params:    {', '.join(stats['swept_params'])}")

    if stats['fixed_params']:
        fixed_str = ", ".join(f"{k}={v}" for k, v in stats['fixed_params'].items())
        lines.append(f"Fixed params:    {fixed_str}")

    lines.append("")
    lines.append("RESULTS BY SOLVER")
    lines.append("-" * 40)

    for solver in stats['solvers']:
        lines.append(f"\n{solver.upper()}:")
        lines.append(f"  Max k-eff:     {stats[f'{solver}_max_keff']:.5f}")
        lines.append(f"  Max k+2σ:      {stats[f'{solver}_max_k2s']:.5f}")

        status = stats[f'{solver}_status']
        status_str = ", ".join(f"{k}: {v}" for k, v in status.items())
        lines.append(f"  Status:        {status_str}")

    # Overall safety assessment
    lines.append("")
    lines.append("SAFETY ASSESSMENT")
    lines.append("-" * 40)

    max_k2s = max(stats.get(f"{s}_max_k2s", 0) for s in stats['solvers'])
    if max_k2s < 0.95:
        lines.append(f"✓ ALL CASES SAFE (max k+2σ = {max_k2s:.5f} < 0.95)")
    elif max_k2s < 1.0:
        lines.append(f"⚠ MARGINAL CASES PRESENT (max k+2σ = {max_k2s:.5f})")
    else:
        lines.append(f"✗ CRITICAL CASES PRESENT (max k+2σ = {max_k2s:.5f} >= 1.0)")

    return "\n".join(lines)
