#!/usr/bin/env python3
"""Print `mu` for ORNL/TM-12292 Eq. (A.1) UO2F2 physics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from critbuddy.core.materials.uo2f2_physics import uranium_molar_mass


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print mu (average uranium molar mass) for UO2F2 Eq. (A.1)."
    )
    parser.add_argument(
        "--enrichment",
        type=float,
        default=20.0,
        help="U-235 weight percent. Default: 20.0",
    )
    args = parser.parse_args()

    mu = uranium_molar_mass(args.enrichment)
    print(f"enrichment_wt_pct={args.enrichment:.6g}")
    print(f"mu_g_per_mol={mu:.12f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
