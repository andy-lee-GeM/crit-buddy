#!/usr/bin/env python3
"""Print UO2F2 densities for a standard H/U sweep."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from critbuddy.core.uo2f2_physics import uo2f2_density
except Exception as exc:
    raise SystemExit(
        "Failed to import critbuddy.core.uo2f2_physics. Run this script with the openmc-env interpreter."
    ) from exc


DEFAULT_H_TO_U_VALUES = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 20.0, 30.0, 40.0, 50.0]


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _print_table(enrichment_pct: float, h_to_u_values: list[float]) -> None:
    title = f"UO2F2 density sweep for enrichment {enrichment_pct:g} wt% U-235"
    print(title)
    print("=" * len(title))
    print(f"{'H/U':>8} {'Density (g/cc)':>16}")
    print("-" * 25)
    for h_to_u in h_to_u_values:
        print(f"{h_to_u:8.3f} {uo2f2_density(h_to_u, enrichment_pct=enrichment_pct):16.6f}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Print UO2F2 densities for a standard H/U sweep")
    parser.add_argument(
        "--enrichment",
        type=float,
        default=5.0,
        help="U-235 wt%% enrichment (default: 5.0)",
    )
    parser.add_argument(
        "--h-to-u-values",
        type=_parse_float_list,
        default=DEFAULT_H_TO_U_VALUES,
        help="Comma-separated H/U values (default: 1,2,3,4,5,6,7,8,9,10,20,30,40,50)",
    )
    args = parser.parse_args()

    _print_table(args.enrichment, args.h_to_u_values)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
