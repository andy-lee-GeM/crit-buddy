#!/usr/bin/env python3
"""
Run a tiny cascade-array OpenMC smoke test.

This script runs a single low-history case and prints:
1) k-eff result
2) boundary surface lines for x_min/x_max/y_min/y_max/z_min/z_max
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from critbuddy.core.config import ExperimentConfig, generate_cases
from critbuddy.core.template_loader import load_template_class
from critbuddy.solvers.openmc.solver import OpenMCSolver


BOUNDARY_NAMES = {"x_min", "x_max", "y_min", "y_max", "z_min", "z_max"}


def _default_config() -> dict:
    return {
        "problem": "cascade_array",
        "name": "cascade smoke",
        "enrichment": 5.0,
        "fissile_material": "uf6",
        "R_inner_cm": 5.0,
        "H_inner_cm": 30.0,
        "t_wall_cm": 0.3175,
        "wall_material": "steel",
        "i": 2,
        "j": 2,
        "k": 1,
        "gap_xy_cm": 3.0,
        "gap_z_cm": 10.0,
        "environment_material": "air",
        "reflector_thickness_cm": 10.0,
    }


def _load_cross_sections_from_repo_config() -> None:
    """Set OPENMC_CROSS_SECTIONS from config.yaml when available."""
    if os.getenv("OPENMC_CROSS_SECTIONS"):
        return

    config_path = ROOT / "config.yaml"
    if not config_path.exists():
        return

    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh) or {}

    xs_path = config.get("openmc_cross_sections")
    if xs_path and Path(xs_path).exists():
        os.environ["OPENMC_CROSS_SECTIONS"] = xs_path


def _print_boundary_lines(geometry_xml: Path) -> None:
    if not geometry_xml.exists():
        print(f"geometry.xml not found at {geometry_xml}")
        return

    print("\nBoundary surfaces from geometry.xml:")
    pattern = re.compile(r'name="([^"]+)"')
    with geometry_xml.open("r", encoding="utf-8") as fh:
        for line in fh:
            if "<surface " not in line:
                continue
            match = pattern.search(line)
            if not match:
                continue
            name = match.group(1)
            if name in BOUNDARY_NAMES:
                print(line.rstrip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny cascade-array smoke test")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "tmp" / "cascade_smoke"),
        help="Directory for case output",
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Show OpenMC progress output",
    )
    args = parser.parse_args()
    _load_cross_sections_from_repo_config()

    cfg = ExperimentConfig.from_dict(_default_config())
    template = load_template_class("cascade_array")
    cases = generate_cases(cfg, template, smoke_test=True)  # 5000 particles, 50 batches, 10 inactive
    case = cases[0]

    solver = OpenMCSolver(show_progress=args.show_progress)
    if not solver.is_available():
        print("OpenMC Python package is not available in this environment.")
        return 1

    case_dir = Path(args.output_dir) / "case_1" / "openmc"
    params = {**case.all_params, "CASE_LABEL": case.label}

    result = solver.run(
        params=params,
        case_label=case.label,
        case_dir=case_dir,
        template_dir=ROOT / "templates" / "cascade_array",
        safety_limit=template.SAFETY_LIMIT,
    )

    print(f"status: {result.status.value}")
    if result.errors:
        print(f"error: {result.errors[0]}")
        return 2

    print(f"keff: {result.keff:.5f} +/- {result.uncertainty:.5f}")
    print(f"k+2sigma: {result.k2sigma:.5f}")
    print(f"case_dir: {case_dir.resolve()}")

    _print_boundary_lines(case_dir / "geometry.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
