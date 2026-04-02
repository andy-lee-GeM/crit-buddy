#!/usr/bin/env python3
"""Build or refresh a local handoff package under handoffs/<model>/."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _handoff_common import DEFAULT_OUTPUT_ROOT, get_model_spec, package_root
from build_handoff_report import build_handoff_report
from collect_handoff_artifacts import collect_handoff_artifacts
from export_material_cards import export_materials


def create_handoff_repo(model_name: str, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    get_model_spec(model_name)
    out_root = package_root(output_root, model_name)
    out_root.mkdir(parents=True, exist_ok=True)
    build_handoff_report(model_name, output_root)
    collect_handoff_artifacts(model_name, output_root)
    export_materials(out_root / "materials")
    return out_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="+")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()

    for model_name in args.models:
        out_root = create_handoff_repo(model_name, args.output_root)
        print(out_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
