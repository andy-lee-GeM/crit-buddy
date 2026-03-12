#!/usr/bin/env python3
"""Print MCNP-oriented material tables derived from OpenMC materials."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from openmc.data import zam

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from critbuddy.core import materials as lib
    from critbuddy.core.material_conversions import summarize_openmc_material
except Exception as exc:
    raise SystemExit(
        "Failed to import critbuddy.core materials. Run this script with the openmc-env interpreter."
    ) from exc

Builder = Callable[[argparse.Namespace], object]
DEFAULT_UF6_ENRICHMENTS = [5.0, 10.0, 15.0, 20.0]
DEFAULT_UO2F2_ENRICHMENTS = [5.0, 10.0, 15.0, 20.0]
DEFAULT_H_TO_U_VALUES = [0.0, 2.0, 10.0, 30.0, 100.0]


def _builders() -> dict[str, Builder]:
    return {
        "aluminum": lambda a: lib.aluminum(),
        "steel": lambda a: lib.stainless_steel_316(),
        "ss304": lambda a: lib.stainless_steel_304(),
        "water": lambda a: lib.water(density_g_cm3=a.water_density),
        "concrete": lambda a: lib.concrete_ordinary(),
        "air": lambda a: lib.air_dry(),
        "humid_air": lambda a: lib.humid_air(),
        "void": lambda a: lib.void(),
        "vacuum": lambda a: lib.vacuum(),
        "uf6": lambda a: lib.create_uf6(a.enrichment, density=a.uf6_density),
        "uo2f2": lambda a: lib.create_uo2f2(
            a.enrichment,
            h_to_u=a.h_to_u,
        ),
    }


def _all_names() -> list[str]:
    return list(_builders().keys())


def _zaid(nuclide: str, suffix: str) -> str:
    z, a, m = zam(nuclide)
    if m != 0:
        raise ValueError(f"Metastable nuclide not supported for ZAID conversion: {nuclide}")
    return f"{1000 * z + a}.{suffix}"


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _format_float_list(values: list[float]) -> str:
    return ", ".join(f"{value:g}" for value in values)


def _requested_enrichments(args: argparse.Namespace) -> list[float]:
    if args.enrichments:
        return args.enrichments
    if not args.use_default_sweeps:
        return [args.enrichment]
    if getattr(args, "_current_material", None) == "uo2f2":
        return DEFAULT_UO2F2_ENRICHMENTS
    return DEFAULT_UF6_ENRICHMENTS


def _requested_h_to_u_values(args: argparse.Namespace) -> list[float]:
    if args.h_to_u_values:
        return args.h_to_u_values
    return DEFAULT_H_TO_U_VALUES if args.use_default_sweeps else [args.h_to_u]


def _material_jobs(args: argparse.Namespace) -> list[tuple[str, object]]:
    builders = _builders()
    names = _all_names() if "all" in args.materials else args.materials

    jobs: list[tuple[str, object]] = []
    for name in names:
        args._current_material = name
        if name == "uf6":
            for enrichment in _requested_enrichments(args):
                args.enrichment = enrichment
                label = f"uf6_enr_{enrichment:.1f}wt"
                jobs.append((label, builders["uf6"](args)))
            continue

        if name == "uo2f2":
            for enrichment in _requested_enrichments(args):
                for h_to_u in _requested_h_to_u_values(args):
                    args.enrichment = enrichment
                    args.h_to_u = h_to_u
                    label = f"uo2f2_enr_{enrichment:.1f}wt_hu_{h_to_u:.1f}"
                    jobs.append((label, builders["uo2f2"](args)))
            continue

        jobs.append((name, builders[name](args)))

    return jobs


def _case_notes(name: str) -> list[str]:
    notes: list[str] = []

    if name.startswith("uf6_enr_"):
        enrichment = name.removeprefix("uf6_enr_").removesuffix("wt")
        notes.append(f"enrichment_wt_pct: {enrichment}")
        notes.append("density_basis: dry_uf6_default")
    elif name.startswith("uo2f2_enr_"):
        rest = name.removeprefix("uo2f2_enr_")
        enrichment, h_to_u = rest.split("_hu_")
        notes.append(f"enrichment_wt_pct: {enrichment.removesuffix('wt')}")
        notes.append(f"h_to_u: {h_to_u}")
        notes.append("density_basis: ORNL_TM_12292_Appendix_A_Eq_A1_plus_uranyl_fluoride_piecewise_fit")

    return notes


def _print_section_header(title: str) -> None:
    line = "=" * 88
    print(f"\n{line}")
    print(title)
    print(line)


def _print_material_block(name: str, mat_num: int, mat, xs_suffix: str) -> None:
    summary = summarize_openmc_material(mat)
    notes = _case_notes(name)

    _print_section_header(f"{name}  |  m{mat_num}")
    print(f"OpenMC name           : {summary.name}")
    print(f"MCNP cell density     : {-float(summary.density_g_cm3):.8e}  g/cc")
    print(f"MCNP atom density     : {float(summary.total_atom_density_bcm):.8e}  atoms/b-cm")
    for note in notes:
        label, value = note.split(": ", maxsplit=1)
        print(f"{label.replace('_', ' ').title():20s}: {value}")

    print("\nNuclide Table")
    print("-" * 88)
    print("nuclide   zaid         atom_density(b-cm)   mass_density(g/cc)   atom_frac    weight_frac")
    print("-" * 88)
    for row in summary.nuclides:
        print(
            f"{row.nuclide:8s}  {_zaid(row.nuclide, xs_suffix):12s}  "
            f"{float(row.atom_density_bcm):17.8e}  {float(row.mass_density_g_cm3):18.8e}  "
            f"{float(row.atom_fraction):11.8f}  {float(row.weight_fraction):12.8f}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print MCNP-oriented material summaries derived from OpenMC materials."
    )
    parser.add_argument(
        "materials",
        nargs="*",
        default=["all"],
        help=f"Names ({', '.join(_all_names())}) or 'all'",
    )
    parser.add_argument(
        "--enrichment",
        type=float,
        default=5.0,
        help="Single U-235 wt%% value for UF6/UO2F2 when not using default sweeps",
    )
    parser.add_argument(
        "--enrichments",
        type=_parse_float_list,
        default=None,
        help="Comma-separated U-235 wt%% values, e.g. 5,10,15,20",
    )
    parser.add_argument(
        "--uf6-density",
        type=float,
        default=5.09,
        help="UF6 density in g/cc (default is dry UF6 density)",
    )
    parser.add_argument(
        "--water-density",
        type=float,
        default=1.0,
        help="Water density in g/cc",
    )
    parser.add_argument(
        "--h-to-u",
        type=float,
        default=0.0,
        help="Single H/U value for UO2F2 when not using default sweeps",
    )
    parser.add_argument(
        "--h-to-u-values",
        type=_parse_float_list,
        default=None,
        help="Comma-separated H/U values for UO2F2, e.g. 0,2,10,30,100",
    )
    parser.add_argument(
        "--no-default-sweeps",
        action="store_false",
        dest="use_default_sweeps",
        help="Use single-point UF6/UO2F2 values instead of the default sweep grid",
    )
    parser.add_argument(
        "--mat-start",
        type=int,
        default=1,
        help="Starting MCNP material number",
    )
    parser.add_argument(
        "--xs-suffix",
        default="80c",
        help="MCNP cross-section suffix, e.g. 80c",
    )
    args = parser.parse_args()

    names = _all_names() if "all" in args.materials else args.materials
    unknown = [name for name in names if name not in _builders()]
    if unknown:
        print(f"Unknown material(s): {', '.join(unknown)}")
        print(f"Available: {', '.join(_all_names())}")
        return 2

    _print_section_header("MCNP Material Helper Output")
    print("Source                : critbuddy/core/materials.py via summarize_openmc_material()")
    print("Static materials      : no extra inputs required")
    print(f"Default UF6 enr (wt%) : {_format_float_list(DEFAULT_UF6_ENRICHMENTS)}")
    print(f"Default UO2F2 enr     : {_format_float_list(DEFAULT_UO2F2_ENRICHMENTS)}")
    print(f"Default UO2F2 H/U     : {_format_float_list(DEFAULT_H_TO_U_VALUES)}")
    print("UF6 density model     : dry default 5.09 g/cc unless overridden")
    print("UO2F2 density model   : ORNL/TM-12292 Appendix A Eq. (A.1) with low-H/U uranyl-fluoride fit")
    print("MCNP density forms    : use either -g/cc or +atoms/b-cm")

    jobs = _material_jobs(args)
    for idx, (name, mat) in enumerate(jobs):
        mat_num = args.mat_start + idx
        _print_material_block(name, mat_num, mat, args.xs_suffix)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
