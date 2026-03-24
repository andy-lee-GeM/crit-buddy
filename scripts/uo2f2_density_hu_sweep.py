#!/usr/bin/env python3
"""Standalone UO2F2 density sweep using crit-buddy's current ORNL-based physics.

This file is plain text and runnable as a Python script:

    python scripts/uo2f2_density_hu_sweep.py

Optional:

    python scripts/uo2f2_density_hu_sweep.py --enrichments 5,10,20,50,100
    python scripts/uo2f2_density_hu_sweep.py --format csv
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ENRICHMENTS = [5.0, 10.0, 20.0, 50.0, 100.0]
DEFAULT_HU_START = 1.0
DEFAULT_HU_STOP = 30.0
DEFAULT_HU_STEP = 1.0


@dataclass(frozen=True)
class IsotopicMasses:
    u235_g_per_mol: float = 235.044
    u238_g_per_mol: float = 238.051
    o16_g_per_mol: float = 15.999
    f19_g_per_mol: float = 18.998403163
    h2o_g_per_mol: float = 18.015


@dataclass(frozen=True)
class UranylFluorideModel:
    n_u_per_formula: float = 1.0
    h_per_h2o: float = 2.0
    waters_of_hydration: float = 2.0
    dihydrate_molar_volume_cm3_per_mol: float = 72.2809
    water_molar_volume_cm3_per_mol: float = 18.0574
    h_over_u_transition: float = 4.0
    rho_u_intercept_g_cm3: float = 4.96
    rho_u_slope_g_cm3_per_hu: float = 0.32


@dataclass(frozen=True)
class UO2F2Stoichiometry:
    enrichment_pct: float
    h_to_u: float
    density_g_cm3: float
    uo2f2_component_density_g_cm3: float
    h2o_component_density_g_cm3: float
    water_weight_fraction: float


ATOMIC_MASSES = IsotopicMasses()
UO2F2_MODEL = UranylFluorideModel()


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _float_range(start: float, stop: float, step: float) -> list[float]:
    if step <= 0.0:
        raise ValueError("step must be positive")
    values: list[float] = []
    current = start
    while current <= stop + 1.0e-12:
        values.append(round(current, 10))
        current += step
    return values


def _uranium_atom_fractions(enrichment_pct: float) -> tuple[float, float]:
    w235 = enrichment_pct / 100.0
    w238 = 1.0 - w235

    n235 = w235 / ATOMIC_MASSES.u235_g_per_mol
    n238 = w238 / ATOMIC_MASSES.u238_g_per_mol
    total = n235 + n238

    return n235 / total, n238 / total


def _uranium_molar_mass(enrichment_pct: float) -> float:
    x235, x238 = _uranium_atom_fractions(enrichment_pct)
    return (
        x235 * ATOMIC_MASSES.u235_g_per_mol
        + x238 * ATOMIC_MASSES.u238_g_per_mol
    )


def _uranium_density(mu: float, h_to_u: float) -> float:
    specific_uc = (
        UO2F2_MODEL.dihydrate_molar_volume_cm3_per_mol
        / UO2F2_MODEL.n_u_per_formula
    )
    specific_water = (
        UO2F2_MODEL.water_molar_volume_cm3_per_mol
        / UO2F2_MODEL.h_per_h2o
    )
    denominator = specific_uc + (
        h_to_u
        - UO2F2_MODEL.h_per_h2o * UO2F2_MODEL.waters_of_hydration
    ) * specific_water
    return mu / denominator


def _uranyl_fluoride_density(mu: float, h_to_u: float) -> float:
    if h_to_u < UO2F2_MODEL.h_over_u_transition:
        return (
            UO2F2_MODEL.rho_u_intercept_g_cm3
            - UO2F2_MODEL.rho_u_slope_g_cm3_per_hu * h_to_u
        )
    return _uranium_density(mu, h_to_u)


def _dry_uo2f2_molar_mass(mu: float) -> float:
    return mu + 2.0 * ATOMIC_MASSES.o16_g_per_mol + 2.0 * ATOMIC_MASSES.f19_g_per_mol


def uo2f2_stoichiometry(h_to_u: float, enrichment_pct: float) -> UO2F2Stoichiometry:
    if h_to_u < 0.0:
        raise ValueError("H/U ratio must be non-negative")
    if enrichment_pct <= 0.0:
        raise ValueError("enrichment must be positive")

    mu = _uranium_molar_mass(enrichment_pct)
    n_water = h_to_u / UO2F2_MODEL.h_per_h2o
    dry_uo2f2_mass = _dry_uo2f2_molar_mass(mu)
    water_mass = n_water * ATOMIC_MASSES.h2o_g_per_mol
    total_mass = dry_uo2f2_mass + water_mass

    rho_u = _uranyl_fluoride_density(mu, h_to_u)
    density = rho_u * total_mass / mu
    total_volume = total_mass / density if density > 0.0 else 0.0

    uo2f2_component_density = dry_uo2f2_mass / total_volume if total_volume > 0.0 else 0.0
    h2o_component_density = water_mass / total_volume if total_volume > 0.0 else 0.0

    return UO2F2Stoichiometry(
        enrichment_pct=enrichment_pct,
        h_to_u=h_to_u,
        density_g_cm3=density,
        uo2f2_component_density_g_cm3=uo2f2_component_density,
        h2o_component_density_g_cm3=h2o_component_density,
        water_weight_fraction=water_mass / total_mass if total_mass > 0.0 else 0.0,
    )


def _region_name(h_to_u: float) -> str:
    return "hydrated_salt" if h_to_u < UO2F2_MODEL.h_over_u_transition else "slurry_or_solution"


def _print_table(enrichments: list[float], h_values: list[float]) -> None:
    print("UO2F2 density sweep using the current crit-buddy ORNL-based physics")
    print(
        "Default enrichments are the validated points in tests: "
        + ", ".join(f"{value:g}" for value in enrichments)
        + " wt% U-235"
    )
    print(
        f"H/U range: {h_values[0]:g} to {h_values[-1]:g} by "
        f"{(h_values[1] - h_values[0]) if len(h_values) > 1 else 0.0:g}"
    )

    for enrichment in enrichments:
        print()
        print("=" * 114)
        print(f"Enrichment = {enrichment:g} wt% U-235")
        print("=" * 114)
        print(
            " H/U    Bulk Density    UO2F2 Comp.    H2O Comp.    Water wt frac    Region"
        )
        print(
            "        (g/cm3)         (g/cm3)        (g/cm3)"
        )
        print("-" * 114)

        for h_to_u in h_values:
            case = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
            print(
                f"{h_to_u:5.1f}  "
                f"{case.density_g_cm3:13.6f}  "
                f"{case.uo2f2_component_density_g_cm3:13.6f}  "
                f"{case.h2o_component_density_g_cm3:11.6f}  "
                f"{case.water_weight_fraction:14.6f}  "
                f"{_region_name(h_to_u)}"
            )


def _print_csv(enrichments: list[float], h_values: list[float]) -> None:
    print(
        "enrichment_wt_pct,h_to_u,bulk_density_g_cm3,uo2f2_component_density_g_cm3,"
        "h2o_component_density_g_cm3,water_weight_fraction,region"
    )
    for enrichment in enrichments:
        for h_to_u in h_values:
            case = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
            print(
                f"{enrichment:.6g},{h_to_u:.6g},{case.density_g_cm3:.8f},"
                f"{case.uo2f2_component_density_g_cm3:.8f},"
                f"{case.h2o_component_density_g_cm3:.8f},"
                f"{case.water_weight_fraction:.8f},{_region_name(h_to_u)}"
            )


def _csv_lines(enrichments: list[float], h_values: list[float]) -> list[str]:
    lines = [
        "enrichment_wt_pct,h_to_u,bulk_density_g_cm3,uo2f2_component_density_g_cm3,"
        "h2o_component_density_g_cm3,water_weight_fraction,region"
    ]
    for enrichment in enrichments:
        for h_to_u in h_values:
            case = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
            lines.append(
                f"{enrichment:.6g},{h_to_u:.6g},{case.density_g_cm3:.8f},"
                f"{case.uo2f2_component_density_g_cm3:.8f},"
                f"{case.h2o_component_density_g_cm3:.8f},"
                f"{case.water_weight_fraction:.8f},{_region_name(h_to_u)}"
            )
    return lines


def _write_csv(csv_path: Path, enrichments: list[float], h_values: list[float]) -> Path:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text("\n".join(_csv_lines(enrichments, h_values)) + "\n", encoding="ascii")
    return csv_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sweep UO2F2 densities over H/U using crit-buddy's current ORNL-based model."
    )
    parser.add_argument(
        "--enrichments",
        type=_parse_float_list,
        default=DEFAULT_ENRICHMENTS,
        help="Comma-separated U-235 wt%% values. Default: 5,10,20,50,100",
    )
    parser.add_argument(
        "--h-start",
        type=float,
        default=DEFAULT_HU_START,
        help="Starting H/U value. Default: 1",
    )
    parser.add_argument(
        "--h-stop",
        type=float,
        default=DEFAULT_HU_STOP,
        help="Ending H/U value. Default: 30",
    )
    parser.add_argument(
        "--h-step",
        type=float,
        default=DEFAULT_HU_STEP,
        help="H/U increment. Default: 1",
    )
    parser.add_argument(
        "--format",
        choices=("table", "csv"),
        default="table",
        help="Output format. Default: table",
    )
    parser.add_argument(
        "--csv",
        nargs="?",
        const="uo2f2_density_hu_sweep.csv",
        default=None,
        help=(
            "Write results to a CSV file. If no path is provided, writes "
            "uo2f2_density_hu_sweep.csv in the current directory."
        ),
    )
    args = parser.parse_args()

    h_values = _float_range(args.h_start, args.h_stop, args.h_step)
    if not h_values:
        raise ValueError("No H/U values were generated from the requested range")

    if args.csv is not None:
        output_path = _write_csv(Path(args.csv), args.enrichments, h_values)
        print(f"Wrote CSV: {output_path.resolve()}")
    elif args.format == "csv":
        _print_csv(args.enrichments, h_values)
    else:
        _print_table(args.enrichments, h_values)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
