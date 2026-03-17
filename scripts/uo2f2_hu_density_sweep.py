#!/usr/bin/env python3
"""Print a UO2F2 H/U density sweep derived from ORNL/TM-12292 Appendix A."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from critbuddy.core.materials import uo2f2_stoichiometry
except Exception as exc:
    raise SystemExit(
        "Failed to import critbuddy.core.materials. Run inside the OpenMC env with project root on PYTHONPATH."
    ) from exc

DEFAULT_H_TO_U_VALUES = [0.0, 2.0, 10.0, 30.0, 100.0]


def _coerce_h_to_u_values(args: argparse.Namespace) -> list[float]:
    if args.h_to_u:
        return args.h_to_u

    if args.range:
        start, stop, step = args.range
        if step <= 0:
            raise SystemExit("--range step must be positive")

        values = []
        current = start
        while current <= stop + 1e-9:
            values.append(round(current, 10))
            current += step
        return values

    return [float(value) for value in DEFAULT_H_TO_U_VALUES]


def _rows(h_to_u_values: list[float], enrichment: float) -> list[dict[str, float]]:
    rows = []
    for h_to_u in h_to_u_values:
        stoich = uo2f2_stoichiometry(h_to_u, enrichment_pct=enrichment)
        rows.append(
            {
                "h_to_u": stoich.h_to_u,
                "density_g_cm3": stoich.density_g_cm3,
                "water_moles_per_u": stoich.water_moles_per_u,
                "water_wt_frac": stoich.water_weight_fraction,
                "molar_mass_g_per_mol": stoich.molar_mass_g_per_mol,
                "molar_volume_cm3_per_mol": stoich.molar_volume_cm3_per_mol,
            }
        )
    return rows


def _print_table(rows: list[dict[str, float]]) -> None:
    header = (
        f"{'H/U':>8} {'Density (g/cc)':>16} {'H2O mol/U':>12} "
        f"{'H2O wt frac':>12} {'MW (g/mol)':>12} {'Vol (cc/mol)':>14}"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['h_to_u']:8.3f} {row['density_g_cm3']:16.6f} "
            f"{row['water_moles_per_u']:12.3f} {row['water_wt_frac']:12.6f} "
            f"{row['molar_mass_g_per_mol']:12.3f} {row['molar_volume_cm3_per_mol']:14.3f}"
        )


def _write_csv(rows: list[dict[str, float]], output_path: Path) -> None:
    fieldnames = list(rows[0].keys())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a UO2F2 H/U density sweep table")
    parser.add_argument(
        "--enrichment",
        type=float,
        default=20.0,
        help="U-235 wt%% enrichment",
    )
    parser.add_argument(
        "--h-to-u",
        nargs="+",
        type=float,
        help="Explicit H/U values to evaluate",
    )
    parser.add_argument(
        "--range",
        nargs=3,
        metavar=("START", "STOP", "STEP"),
        type=float,
        help="Generate H/U values over an inclusive numeric range",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Optional CSV output path",
    )
    args = parser.parse_args()

    h_to_u_values = _coerce_h_to_u_values(args)
    rows = _rows(h_to_u_values, args.enrichment)

    _print_table(rows)

    if args.csv:
        _write_csv(rows, args.csv)
        print(f"\nSaved CSV: {args.csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
