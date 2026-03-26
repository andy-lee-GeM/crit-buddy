#!/usr/bin/env python3
"""Print MCNP-oriented material tables derived from OpenMC materials."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from openmc.data import zam

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from critbuddy.core import materials as lib
    from critbuddy.core.materials.material_properties import summarize_openmc_material
    from critbuddy.core.materials.uo2f2_physics import uo2f2_density as derive_uo2f2_density
except Exception as exc:
    raise SystemExit(
        "Failed to import critbuddy.core materials. Run this script with the openmc-env interpreter."
    ) from exc

Builder = Callable[[argparse.Namespace], object]
DEFAULT_SINGLE_ENRICHMENT = 5.0
DEFAULT_UF6_ENRICHMENTS = [5.0, 10.0, 15.0, 20.0]
DEFAULT_UO2F2_ENRICHMENTS = [5.0, 10.0, 15.0, 20.0]
DEFAULT_UF6_DENSITY = 5.09
DEFAULT_DRY_UO2F2_DENSITY = 6.37

NOTE_LABELS = {
    "enrichment_wt_pct": "Enrichment Wt Pct",
    "density_basis": "Density Basis",
    "h_to_u": "H/U",
}


@dataclass(frozen=True)
class MaterialJob:
    label: str
    material: object
    notes: tuple[str, ...] = ()


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
    }


def _all_names() -> list[str]:
    return [*_builders().keys(), "uf6", "uo2f2"]


def _zaid(nuclide: str, suffix: str) -> str:
    z, a, m = zam(nuclide)
    if m != 0:
        raise ValueError(f"Metastable nuclide not supported for ZAID conversion: {nuclide}")
    return f"{1000 * z + a}.{suffix}"


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _format_float_list(values: list[float]) -> str:
    return ", ".join(f"{value:g}" for value in values)


def _single_point_enrichment(args: argparse.Namespace) -> float:
    return DEFAULT_SINGLE_ENRICHMENT if args.enrichment is None else args.enrichment


def _requested_enrichments(material_name: str, args: argparse.Namespace) -> list[float]:
    if args.enrichments:
        return args.enrichments
    if (
        material_name == "uo2f2"
        and args.h_to_u is not None
        and args.enrichment is not None
    ):
        return [args.enrichment]
    if not args.use_default_sweeps:
        return [_single_point_enrichment(args)]
    if material_name == "uo2f2":
        return DEFAULT_UO2F2_ENRICHMENTS
    return DEFAULT_UF6_ENRICHMENTS


def _resolve_uo2f2_inputs(
    args: argparse.Namespace,
    enrichment: float,
) -> tuple[float, float, str]:
    h_to_u = 0.0 if args.h_to_u is None else args.h_to_u
    if args.uo2f2_density is not None:
        return h_to_u, args.uo2f2_density, "user_specified_uo2f2_density"
    if args.h_to_u is not None:
        return (
            h_to_u,
            derive_uo2f2_density(h_to_u, enrichment_pct=enrichment),
            "derived_from_h_to_u",
        )
    return h_to_u, DEFAULT_DRY_UO2F2_DENSITY, "default_dry_uo2f2_density"


def _material_jobs(args: argparse.Namespace) -> list[MaterialJob]:
    builders = _builders()
    names = _all_names() if "all" in args.materials else args.materials

    jobs: list[MaterialJob] = []
    for name in names:
        if name == "uf6":
            for enrichment in _requested_enrichments(name, args):
                label = f"uf6_enr_{enrichment:.1f}wt"
                notes = (
                    f"enrichment_wt_pct: {enrichment}",
                    "density_basis: dry_uf6_default",
                )
                jobs.append(
                    MaterialJob(
                        label=label,
                        material=lib.uf6(enrichment, density=args.uf6_density),
                        notes=notes,
                    )
                )
            continue

        if name == "uo2f2":
            for enrichment in _requested_enrichments(name, args):
                h_to_u, density, density_basis = _resolve_uo2f2_inputs(args, enrichment)
                label = f"uo2f2_enr_{enrichment:.1f}wt"
                notes = (
                    f"enrichment_wt_pct: {enrichment}",
                    f"h_to_u: {h_to_u}",
                    f"density_basis: {density_basis}",
                )
                jobs.append(
                    MaterialJob(
                        label=label,
                        material=lib.uo2f2(enrichment, h_to_u=h_to_u, density=density),
                        notes=notes,
                    )
                )
            continue

        jobs.append(MaterialJob(label=name, material=builders[name](args)))

    return jobs


def _print_section_header(title: str) -> None:
    line = "=" * 88
    print(f"\n{line}")
    print(title)
    print(line)


def _format_note(note: str) -> str:
    label, value = note.split(": ", maxsplit=1)
    display_label = NOTE_LABELS.get(label, label.replace("_", " ").title())
    return f"{display_label:20s}: {value}"


def _print_material_block(
    name: str,
    mat_num: int,
    mat,
    xs_suffix: str,
    notes: tuple[str, ...] = (),
) -> None:
    summary = summarize_openmc_material(mat)

    _print_section_header(f"{name}  |  m{mat_num}")
    print(f"OpenMC name           : {summary.name}")
    print(f"Bulk density          : {float(summary.density_g_cm3):.8e}  g/cc")
    print(f"MCNP cell density     : {-float(summary.density_g_cm3):.8e}  g/cc")
    print(f"MCNP atom density     : {float(summary.total_atom_density_bcm):.8e}  atoms/b-cm")
    for note in notes:
        print(_format_note(note))

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
        "-enrichment",
        "-e",
        type=float,
        default=None,
        help=(
            "Single U-235 wt%% value for single-point UF6/UO2F2 cases. "
            "Defaults to 5.0 wt%% when --no-default-sweeps is used without an explicit value."
        ),
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
        default=DEFAULT_UF6_DENSITY,
        help="UF6 density in g/cc (default is dry UF6 density)",
    )
    parser.add_argument(
        "--water-density",
        type=float,
        default=1.0,
        help="Water density in g/cc",
    )
    parser.add_argument(
        "--uo2f2-density",
        type=float,
        default=None,
        help=(
            "Explicit UO2F2 bulk density in g/cc. If omitted and H/U is supplied, "
            "density is derived from crit-buddy's ORNL UO2F2 model."
        ),
    )
    parser.add_argument(
        "--h-to-u",
        "--hu",
        "-hu",
        type=float,
        dest="h_to_u",
        default=None,
        help=(
            "UO2F2 hydrogen-to-uranium ratio. When paired with enrichment, "
            "UO2F2 bulk density is derived automatically unless overridden."
        ),
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
    unknown = [name for name in names if name not in _all_names()]
    if unknown:
        print(f"Unknown material(s): {', '.join(unknown)}")
        print(f"Available: {', '.join(_all_names())}")
        return 2

    _print_section_header("MCNP Material Helper Output")
    print("Source                : critbuddy/core/materials/ via critbuddy.core.materials.material_properties")
    print("Static materials      : no extra inputs required")
    print(f"Default UF6 enr (wt%) : {_format_float_list(DEFAULT_UF6_ENRICHMENTS)}")
    print(f"Default UO2F2 enr     : {_format_float_list(DEFAULT_UO2F2_ENRICHMENTS)}")
    print("UF6 density model     : dry default 5.09 g/cc unless overridden")
    print("UO2F2 density model   : derived from H/U when supplied, else dry default 6.37 g/cc")
    print("MCNP density forms    : use either -g/cc or +atoms/b-cm")

    jobs = _material_jobs(args)
    for idx, job in enumerate(jobs):
        mat_num = args.mat_start + idx
        _print_material_block(job.label, mat_num, job.material, args.xs_suffix, job.notes)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
