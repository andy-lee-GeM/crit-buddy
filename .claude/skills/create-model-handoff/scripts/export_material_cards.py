#!/usr/bin/env python3
"""Export the full material library in markdown and MCNP-card text formats."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _handoff_common import ROOT, ensure_parent


def _run_material_dump(args: list[str]) -> str:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "list_mcnp_materials.py"), *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def export_materials(output_dir: Path) -> None:
    markdown_path = output_dir / "material-library.md"
    text_path = output_dir / "mcnp-material-cards.txt"
    ensure_parent(markdown_path)
    ensure_parent(text_path)

    markdown = _run_material_dump(["--format", "markdown"])
    text = _run_material_dump([])

    markdown_path.write_text(
        "# Material Library\n\n"
        "This file is a full shared-library dump generated from "
        "`scripts/list_mcnp_materials.py --format markdown`.\n\n"
        + markdown,
        encoding="utf-8",
    )
    text_path.write_text(
        "c Full shared-library dump generated from "
        "`scripts/list_mcnp_materials.py`\n\n" + text,
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    export_materials(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
