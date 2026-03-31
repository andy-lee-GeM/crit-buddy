#!/usr/bin/env python3
"""List all standard materials and UO2F2 lookup tables in MCNP format.

This script generates MCNP-ready material cards for:
1. All static materials from the standard library (water, steel, aluminum, etc.)
2. UO2F2 materials across H/U ratios and enrichments

Usage:
    python scripts/list_mcnp_materials.py
    python scripts/list_mcnp_materials.py --format markdown
    python scripts/list_mcnp_materials.py --xs-suffix 70c
    python scripts/list_mcnp_materials.py --enrichments 5,10,20
    python scripts/list_mcnp_materials.py --hu-range 0,30,2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from critbuddy.core.materials import MCNPMaterial
    from critbuddy.core.materials.material_specs import STATIC_MATERIAL_SPECS
    from critbuddy.core.materials.builders import get_material, uo2f2
    from critbuddy.core.materials.uo2f2_physics import uo2f2_density, uo2f2_stoichiometry
except ImportError as exc:
    raise SystemExit(
        "Failed to import critbuddy.core.materials. "
        "Run this script with the openmc-env interpreter."
    ) from exc


# ============================================================================
# Default Parameters
# ============================================================================

DEFAULT_XS_SUFFIX = "80c"
DEFAULT_UO2F2_ENRICHMENTS = [5.0, 10.0, 20.0, 50.0, 100.0]
DEFAULT_HU_START = 0.0
DEFAULT_HU_STOP = 30.0
DEFAULT_HU_STEP = 2.0


# ============================================================================
# Formatting Functions
# ============================================================================

def print_section_header(title: str, char: str = "=") -> None:
    """Print section header."""
    line = char * 88
    print(f"\n{line}")
    print(title)
    print(line)


def print_mcnp_material_card(mcnp: MCNPMaterial, mat_num: int) -> None:
    """Print MCNP material card in standard format."""
    print(f"\nc --- Material {mat_num}: {mcnp.name}")
    print(f"c     Bulk density      : {mcnp.bulk_density_g_cm3:.8e} g/cm³")
    print(f"c     Cell density      : {mcnp.cell_density_g_cm3:.8e} g/cm³ (negative)")
    print(f"c     Atom density      : {mcnp.cell_density_bcm:.8e} atoms/b-cm (positive)")
    print(f"c     Cross-section lib : {mcnp.xs_suffix}")
    print(f"m{mat_num}", end="")

    for nuc in mcnp.nuclides:
        print(f"  {nuc.zaid:12s}  {nuc.atom_density_bcm:17.8e}    $ {nuc.nuclide}")


def print_markdown_material_table(mcnp: MCNPMaterial) -> None:
    """Print material as markdown table."""
    print(f"\n### {mcnp.name}")
    print(f"\n**Bulk Density:** {mcnp.bulk_density_g_cm3:.6f} g/cm³  ")
    print(f"**MCNP Cell Density:** {mcnp.cell_density_g_cm3:.8e} g/cm³ (or {mcnp.cell_density_bcm:.8e} atoms/b-cm)")
    print(f"\n| Nuclide | ZAID | Atom Density (atoms/b-cm) | Atom Fraction | Weight Fraction |")
    print(f"|---------|------|---------------------------|---------------|-----------------|")

    for nuc in mcnp.nuclides:
        print(f"| {nuc.nuclide:7s} | {nuc.zaid:12s} | {nuc.atom_density_bcm:.8e} | "
              f"{nuc.atom_fraction:.6f} | {nuc.weight_fraction:.6f} |")


def print_uo2f2_hu_table_terminal(
    enrichments: list[float],
    h_u_values: list[float],
    xs_suffix: str,
) -> None:
    """Print UO2F2 H/U density table for terminal."""
    print_section_header("UO2F2 H/U Density Lookup Table", "=")
    print(f"Cross-section library: {xs_suffix}")
    print(f"Enrichments: {', '.join(f'{e:.1f}%' for e in enrichments)}")
    print(f"H/U range: {h_u_values[0]:.1f} to {h_u_values[-1]:.1f} "
          f"(step: {h_u_values[1] - h_u_values[0] if len(h_u_values) > 1 else 0:.1f})")

    for enrichment in enrichments:
        print(f"\n{'=' * 88}")
        print(f"Enrichment: {enrichment:.1f} wt% U-235")
        print('=' * 88)
        print(f"{'H/U':>6s}  {'ρ_U':>10s}  {'Bulk Mix':>10s}  {'UO2F2':>10s}  "
              f"{'H2O':>10s}  {'H2O wt%':>8s}  {'Region':>15s}")
        print('-' * 88)

        for h_to_u in h_u_values:
            stoich = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
            region = "hydrated_salt" if h_to_u < 4.0 else "slurry/solution"

            print(f"{h_to_u:6.1f}  "
                  f"{stoich.uranium_density_g_cm3:10.4f}  "
                  f"{stoich.density_g_cm3:10.4f}  "
                  f"{stoich.uo2f2_component_density_g_cm3:10.4f}  "
                  f"{stoich.h2o_component_density_g_cm3:10.4f}  "
                  f"{stoich.water_weight_fraction * 100:8.2f}  "
                  f"{region:>15s}")


def print_uo2f2_hu_table_markdown(
    enrichments: list[float],
    h_u_values: list[float],
    xs_suffix: str,
) -> None:
    """Print UO2F2 H/U density table as markdown."""
    print(f"\n## UO2F2 H/U Density Lookup Table\n")
    print(f"**Cross-section library:** {xs_suffix}  ")
    print(f"**Enrichments:** {', '.join(f'{e:.1f}%' for e in enrichments)}  ")
    print(f"**H/U range:** {h_u_values[0]:.1f} to {h_u_values[-1]:.1f}\n")

    for enrichment in enrichments:
        print(f"\n### Enrichment: {enrichment:.1f} wt% U-235\n")
        print(f"| H/U | ρ_U (g/cm³) | Bulk Mix (g/cm³) | UO2F2 (g/cm³) | "
              f"H2O (g/cm³) | H2O wt% | Region |")
        print(f"|-----|-------------|------------------|---------------|-------------|---------|--------|")

        for h_to_u in h_u_values:
            stoich = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
            region = "hydrated_salt" if h_to_u < 4.0 else "slurry/solution"

            print(f"| {h_to_u:.1f} | "
                  f"{stoich.uranium_density_g_cm3:.4f} | "
                  f"{stoich.density_g_cm3:.4f} | "
                  f"{stoich.uo2f2_component_density_g_cm3:.4f} | "
                  f"{stoich.h2o_component_density_g_cm3:.4f} | "
                  f"{stoich.water_weight_fraction * 100:.2f}% | "
                  f"{region} |")


# ============================================================================
# Main Functions
# ============================================================================

def dump_static_materials(xs_suffix: str, output_format: str) -> None:
    """Dump all static materials from the standard library."""
    print_section_header("Standard Materials Library", "=")

    mat_num = 1
    for key in sorted(STATIC_MATERIAL_SPECS.keys()):
        try:
            mat = get_material(key)
            mcnp = MCNPMaterial.from_openmc(mat, xs_suffix=xs_suffix)

            if output_format == "markdown":
                print_markdown_material_table(mcnp)
            else:
                print_mcnp_material_card(mcnp, mat_num)

            mat_num += 1
        except Exception as e:
            print(f"Warning: Could not convert material '{key}': {e}", file=sys.stderr)


def dump_uo2f2_materials(
    enrichments: list[float],
    h_u_values: list[float],
    xs_suffix: str,
    output_format: str,
) -> None:
    """Dump UO2F2 materials for selected H/U and enrichments."""
    if output_format == "markdown":
        print_uo2f2_hu_table_markdown(enrichments, h_u_values, xs_suffix)
    else:
        print_uo2f2_hu_table_terminal(enrichments, h_u_values, xs_suffix)

    # Print a few example material cards
    if output_format != "markdown":
        print_section_header("Example UO2F2 Material Cards", "=")
        print("\nShowing example cards for selected H/U ratios:")

        mat_num = 100
        example_hu = [0.0, 10.0, 20.0]
        example_enr = enrichments[0] if enrichments else 5.0

        for h_to_u in example_hu:
            if h_to_u in h_u_values or h_to_u == 0.0:
                density = uo2f2_density(h_to_u=h_to_u, enrichment_pct=example_enr)
                mat = uo2f2(enrichment_pct=example_enr, h_to_u=h_to_u, density=density)
                mcnp = MCNPMaterial.from_openmc(mat, xs_suffix=xs_suffix)
                print_mcnp_material_card(mcnp, mat_num)
                mat_num += 1


def parse_float_list(value: str) -> list[float]:
    """Parse comma-separated float list."""
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def float_range(start: float, stop: float, step: float) -> list[float]:
    """Generate float range."""
    if step <= 0.0:
        raise ValueError("step must be positive")
    values: list[float] = []
    current = start
    while current <= stop + 1.0e-12:
        values.append(round(current, 10))
        current += step
    return values


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dump all standard materials and UO2F2 lookup tables in MCNP format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--format",
        choices=["terminal", "markdown"],
        default="terminal",
        help="Output format (default: terminal)",
    )

    parser.add_argument(
        "--xs-suffix",
        default=DEFAULT_XS_SUFFIX,
        help=f"MCNP cross-section suffix (default: {DEFAULT_XS_SUFFIX})",
    )

    parser.add_argument(
        "--enrichments",
        type=parse_float_list,
        default=DEFAULT_UO2F2_ENRICHMENTS,
        help=f"Comma-separated UO2F2 enrichments in wt%% "
             f"(default: {','.join(str(e) for e in DEFAULT_UO2F2_ENRICHMENTS)})",
    )

    parser.add_argument(
        "--hu-range",
        type=parse_float_list,
        default=None,
        help=f"H/U range as start,stop,step "
             f"(default: {DEFAULT_HU_START},{DEFAULT_HU_STOP},{DEFAULT_HU_STEP})",
    )

    parser.add_argument(
        "--static-only",
        action="store_true",
        help="Only dump static materials (skip UO2F2)",
    )

    parser.add_argument(
        "--uo2f2-only",
        action="store_true",
        help="Only dump UO2F2 tables (skip static materials)",
    )

    args = parser.parse_args()

    # Parse H/U range
    if args.hu_range:
        if len(args.hu_range) != 3:
            print("Error: --hu-range requires exactly 3 values: start,stop,step")
            return 1
        h_u_values = float_range(args.hu_range[0], args.hu_range[1], args.hu_range[2])
    else:
        h_u_values = float_range(DEFAULT_HU_START, DEFAULT_HU_STOP, DEFAULT_HU_STEP)

    # Print header
    if args.format == "markdown":
        print("# MCNP Materials Reference")
        print("\nGenerated from crit-buddy materials library.")
        print(f"\n**Cross-section library:** {args.xs_suffix}")
    else:
        print("=" * 88)
        print("MCNP Materials Reference")
        print("Generated from crit-buddy materials library")
        print(f"Cross-section library: {args.xs_suffix}")
        print("=" * 88)

    # Dump materials
    if not args.uo2f2_only:
        dump_static_materials(args.xs_suffix, args.format)

    if not args.static_only:
        dump_uo2f2_materials(args.enrichments, h_u_values, args.xs_suffix, args.format)

    # Footer
    if args.format != "markdown":
        print("\n" + "=" * 88)
        print("Complete!")
        print("=" * 88)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
