#!/usr/bin/env python3
"""Copy the canonical handoff markdown and generate the package docx report."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from _handoff_common import DEFAULT_OUTPUT_ROOT, get_model_spec, package_root, write_text
from critbuddy.reporting.docx_generator import generate_calculation_docx


def build_handoff_report(model_name: str, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    spec = get_model_spec(model_name)
    out_root = package_root(output_root, model_name)
    report_dir = out_root / "report"
    report_dir.mkdir(parents=True, exist_ok=True)

    report_md = report_dir / "handoff.md"
    report_docx = report_dir / "handoff.docx"

    report_md.write_text(spec.handoff_md.read_text(encoding="utf-8"), encoding="utf-8")
    generate_calculation_docx(report_md, report_docx)

    readme = f"""# {spec.title} Handoff Package

This directory contains the locally generated handoff package for
`{spec.name}`.

Generated date: {date.today().isoformat()}

Contents:

- `report/` reviewer-facing markdown and docx report
- `models/` runnable OpenMC and MCNP reference models
- `materials/` shared material-library dump and MCNP material cards
- `figures/` selected benchmark and sensitivity plots
- `artifacts/` selected summary inputs and reports
- `data/` heavier copied benchmark and study artifacts
"""
    write_text(out_root / "README.md", readme)
    return report_md


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args()
    build_handoff_report(args.model, args.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
