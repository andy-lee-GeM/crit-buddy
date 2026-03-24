#!/usr/bin/env python3
"""
Render an MCNP xz-crossing reference deck using the OpenMC builder materials as
the source of truth.

This keeps geometry fixed to the canonical gap=0 reference cell while deriving
the MCNP material cards from the current OpenMC builders:
- UF6 gas
- Aluminum wall
- Water moderator
- UO2F2 fuel
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openmc.data import zam

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from critbuddy.core.materials.builders import aluminum, uf6, uo2f2, water
from critbuddy.core.materials.material_properties import summarize_openmc_material


GEOMETRY_BLOCK = """Piping Model- Infinite Lattice (OpenMC builder materials)
c
c Cell Cards
c
1 2 -2.70 2 -1 16 -15 imp:n=1
3 3 -1.0 -7 8 1 -17 18 13 16 -15 imp:n=1
4 5 -6.37 11 -2 16 -15 imp:n=1
5 1 -0.0127 -11 16 -15 imp:n=1
6 5 -6.37 14 -12 -17 18 imp:n=1
7 1 -0.0127 -14 -17 18 imp:n=1
8 2 -2.70 12 -13 -17 18 imp:n=1

c Surface Cards
c
1 cz 5.715
2 cz 5.4102
*7 py 20.145
*8 py -8.715
11 cz 4.4102
12 c/x 11.43 0 5.4102
13 c/x 11.43 0 5.715
14 c/x 11.43 0 4.4102
*15 pz 8.715
*16 pz -8.715
*17 px 8.815
*18 px -8.715

c Data Cards
c
c Material Cards
c
"""


def _mcnp_zaid(nuclide: str, suffix: str = ".80c") -> str:
    z, a, metastable = zam(nuclide)
    if metastable:
        raise ValueError(f"Metastable nuclides are not supported in this deck generator: {nuclide}")
    return f"{1000 * z + a}{suffix}"


def _format_material_card(
    material_id: int,
    summary,
    *,
    sab: str | None = None,
    suffix: str = ".80c",
) -> list[str]:
    lines = []
    for idx, row in enumerate(summary.nuclides):
        prefix = f"m{material_id} " if idx == 0 else "     "
        lines.append(f"{prefix}{_mcnp_zaid(row.nuclide, suffix)} {row.atom_density_bcm:.10e}")
    if sab:
        lines.append(f"mt{material_id} {sab}")
    lines.append("c")
    return lines


def build_material_blocks(
    enrichment_pct: float,
    uf6_density_g_cm3: float,
    uo2f2_density_g_cm3: float,
    moderator_density_g_cm3: float,
    xs_suffix: str,
) -> list[str]:
    gas = summarize_openmc_material(uf6(enrichment_pct=enrichment_pct, density=uf6_density_g_cm3))
    wall = summarize_openmc_material(aluminum())
    moderator = summarize_openmc_material(water(density_g_cm3=moderator_density_g_cm3))
    fuel = summarize_openmc_material(
        uo2f2(
            enrichment_pct=enrichment_pct,
            h_to_u=0.0,
            density=uo2f2_density_g_cm3,
        )
    )

    blocks = []
    blocks.extend(_format_material_card(1, gas, suffix=xs_suffix))
    blocks.extend(_format_material_card(2, wall, suffix=xs_suffix))
    blocks.extend(_format_material_card(3, moderator, sab="lwtr.01t", suffix=xs_suffix))
    blocks.extend(_format_material_card(5, fuel, suffix=xs_suffix))
    return blocks


def render_deck(
    output_path: Path,
    enrichment_pct: float,
    uf6_density_g_cm3: float,
    uo2f2_density_g_cm3: float,
    moderator_density_g_cm3: float,
    xs_suffix: str,
) -> None:
    lines = [
        GEOMETRY_BLOCK.rstrip(),
        *build_material_blocks(
            enrichment_pct=enrichment_pct,
            uf6_density_g_cm3=uf6_density_g_cm3,
            uo2f2_density_g_cm3=uo2f2_density_g_cm3,
            moderator_density_g_cm3=moderator_density_g_cm3,
            xs_suffix=xs_suffix,
        ),
        "c Source Term",
        "c",
        "mode n",
        "kcode 4800 1.0 50 200",
        "ksrc 0 0 0",
        "print",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render the MCNP xz-cross parity deck from OpenMC builders."
    )
    default_output = Path(__file__).with_name("openmc_builder_materials.inp")
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--enrichment-pct", type=float, default=20.2)
    parser.add_argument("--uf6-density-g-cm3", type=float, default=0.0127)
    parser.add_argument("--uo2f2-density-g-cm3", type=float, default=6.37)
    parser.add_argument("--moderator-density-g-cm3", type=float, default=1.0)
    parser.add_argument("--xs-suffix", default=".80c")
    args = parser.parse_args()

    render_deck(
        output_path=args.output,
        enrichment_pct=args.enrichment_pct,
        uf6_density_g_cm3=args.uf6_density_g_cm3,
        uo2f2_density_g_cm3=args.uo2f2_density_g_cm3,
        moderator_density_g_cm3=args.moderator_density_g_cm3,
        xs_suffix=args.xs_suffix,
    )
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
