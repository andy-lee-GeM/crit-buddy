#!/usr/bin/env python3
"""Standalone UO2F2 density sweep using crit-buddy's current ORNL-based physics.

The script reports bulk mixture density and component densities against H/U.
When cross-checking ORNL/TM-12292 Table A.3, compare against the table's H/U
column rather than the leading H/X column.

This file is plain text and runnable as a Python script:

    python scripts/uo2f2_density_hu_sweep.py

Optional:

    python scripts/uo2f2_density_hu_sweep.py --enrichments 5,10,20,50,100
    python scripts/uo2f2_density_hu_sweep.py --format csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from critbuddy.core.materials.uo2f2_physics import UO2F2_MODEL, uo2f2_stoichiometry


DEFAULT_ENRICHMENTS = [5.0, 10.0, 20.0, 50.0, 100.0]
DEFAULT_HU_START = 1.0
DEFAULT_HU_STOP = 30.0
DEFAULT_HU_STEP = 1.0
CSV_HEADER = (
    "enr_wt_pct,h_to_u,rho_u_g_cm3,bulk_mix_g_cm3,dry_uo2f2_g_cm3,"
    "h2o_g_cm3,water_wt_frac,region"
)


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


def _region_name(h_to_u: float) -> str:
    return "hydrated_salt" if h_to_u < UO2F2_MODEL.h_over_u_transition else "slurry_or_solution"


def _table_region_name(h_to_u: float) -> str:
    return "hydrated salt" if h_to_u < UO2F2_MODEL.h_over_u_transition else "slurry/solution"


def _print_table(enrichments: list[float], h_values: list[float]) -> None:
    print("UO2F2 density sweep")
    print(
        "rho_u = uranium density from ORNL Eq. A.2/A.3 | "
        "bulk = total UO2F2 + H2O mixture density"
    )
    print(
        f"H/U range: {h_values[0]:g} to {h_values[-1]:g} by "
        f"{(h_values[1] - h_values[0]) if len(h_values) > 1 else 0.0:g}"
    )

    for enrichment in enrichments:
        print()
        title = f"Enrichment: {enrichment:g} wt% U-235"
        print(title)
        print("-" * len(title))
        print(
            f"{'H/U':>5}  {'rho_u':>8}  {'bulk':>8}  {'dry UO2F2':>10}  "
            f"{'H2O':>8}  {'H2O wt%':>8}  region"
        )
        print(
            f"{'':>5}  {'g/cc':>8}  {'g/cc':>8}  {'g/cc':>10}  "
            f"{'g/cc':>8}  {'%':>8}"
        )
        print("-" * 82)

        for h_to_u in h_values:
            case = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
            print(
                f"{h_to_u:5.1f}  "
                f"{case.uranium_density_g_cm3:8.4f}  "
                f"{case.density_g_cm3:8.4f}  "
                f"{case.uo2f2_component_density_g_cm3:10.4f}  "
                f"{case.h2o_component_density_g_cm3:8.4f}  "
                f"{100.0 * case.water_weight_fraction:7.2f}%  "
                f"{_table_region_name(h_to_u)}"
            )


def _print_csv(enrichments: list[float], h_values: list[float]) -> None:
    print(CSV_HEADER)
    for enrichment in enrichments:
        for h_to_u in h_values:
            case = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
            print(
                f"{enrichment:.6g},{h_to_u:.6g},{case.uranium_density_g_cm3:.8f},"
                f"{case.density_g_cm3:.8f},"
                f"{case.uo2f2_component_density_g_cm3:.8f},"
                f"{case.h2o_component_density_g_cm3:.8f},"
                f"{case.water_weight_fraction:.8f},{_region_name(h_to_u)}"
            )


def _csv_lines(enrichments: list[float], h_values: list[float]) -> list[str]:
    lines = [CSV_HEADER]
    for enrichment in enrichments:
        for h_to_u in h_values:
            case = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
            lines.append(
                f"{enrichment:.6g},{h_to_u:.6g},{case.uranium_density_g_cm3:.8f},"
                f"{case.density_g_cm3:.8f},"
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
