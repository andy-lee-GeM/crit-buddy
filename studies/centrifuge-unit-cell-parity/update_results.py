#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

STUDY_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STUDY_DIR.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from critbuddy.solvers.mcnp.parser import MCNPOutputParser

RESULTS_CSV = STUDY_DIR / "results.csv"
REPORT_PATH = STUDY_DIR / "report.md"

FILL_CASES = [
    {"fill_z_cm": 10.0, "source_z_cm": 5.0},
    {"fill_z_cm": 20.0, "source_z_cm": 10.0},
    {"fill_z_cm": 30.0, "source_z_cm": 10.0},
    {"fill_z_cm": 40.0, "source_z_cm": 10.0},
    {"fill_z_cm": 50.0, "source_z_cm": 10.0},
]


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="ascii") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _to_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def collect_openmc_rows() -> list[dict[str, object]]:
    latest_link = STUDY_DIR / "openmc" / "runs" / "study" / "latest"
    if not latest_link.exists():
        return [
            {
                "fill_z_cm": case["fill_z_cm"],
                "source_z_cm": 10.0,
                "solver": "openmc",
                "keff": "",
                "std": "",
                "status": "PENDING",
                "artifact_dir": "",
            }
            for case in FILL_CASES
        ]

    latest_run_dir = latest_link.resolve()
    run_results = latest_run_dir / "results.csv"
    if not run_results.exists():
        raise FileNotFoundError(f"OpenMC results missing: {run_results}")

    rows: list[dict[str, object]] = []
    with open(run_results, newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "fill_z_cm": float(row["fill_z_cm"]),
                    "source_z_cm": float(row["source_z_cm"]),
                    "solver": "openmc",
                    "keff": row["keff"],
                    "std": row["std"],
                    "status": row["status"],
                    "artifact_dir": str(latest_run_dir),
                }
            )
    return rows


def collect_mcnp_rows() -> list[dict[str, object]]:
    parser = MCNPOutputParser()
    rows: list[dict[str, object]] = []

    for case in FILL_CASES:
        fill_value = int(case["fill_z_cm"])
        case_dir = STUDY_DIR / "mcnp" / f"fill_{fill_value}"
        output_file = case_dir / "out"
        if output_file.exists():
            parsed = parser.parse(output_file)
            status = "OK" if parsed.success else "PARSE_FAILED"
            keff = "" if parsed.keff is None else f"{parsed.keff:.5f}"
            std = "" if parsed.uncertainty is None else f"{parsed.uncertainty:.5f}"
        else:
            status = "PENDING"
            keff = ""
            std = ""

        rows.append(
            {
                "fill_z_cm": case["fill_z_cm"],
                "source_z_cm": case["source_z_cm"],
                "solver": "mcnp",
                "keff": keff,
                "std": std,
                "status": status,
                "artifact_dir": str(case_dir),
            }
        )
    return rows


def update_results() -> list[dict[str, object]]:
    rows = collect_openmc_rows() + collect_mcnp_rows()
    rows.sort(key=lambda row: (float(row["fill_z_cm"]), row["solver"]))
    _write_csv(
        RESULTS_CSV,
        rows,
        ["fill_z_cm", "source_z_cm", "solver", "keff", "std", "status", "artifact_dir"],
    )
    return rows


def update_report(rows: list[dict[str, object]]) -> None:
    by_fill: dict[float, dict[str, dict[str, object]]] = {}
    for row in rows:
        by_fill.setdefault(float(row["fill_z_cm"]), {})[str(row["solver"])] = row

    comparison_lines = []
    completed_deltas: list[tuple[float, float]] = []
    for case in FILL_CASES:
        fill = case["fill_z_cm"]
        openmc_row = by_fill.get(fill, {}).get("openmc", {})
        mcnp_row = by_fill.get(fill, {}).get("mcnp", {})

        openmc_keff = _to_float(openmc_row.get("keff"))
        openmc_std = _to_float(openmc_row.get("std"))
        mcnp_keff = _to_float(mcnp_row.get("keff"))
        mcnp_std = _to_float(mcnp_row.get("std"))

        delta_keff = ""
        if None not in (openmc_keff, openmc_std, mcnp_keff, mcnp_std):
            delta = openmc_keff - mcnp_keff
            delta_keff = f"{delta:+.5f}"
            completed_deltas.append(abs(delta))

        comparison_lines.append(
            "| "
            + " | ".join(
                [
                    str(int(fill)),
                    mcnp_row.get("keff", "") or "",
                    openmc_row.get("keff", "") or "",
                    mcnp_row.get("std", "") or "",
                    openmc_row.get("std", "") or "",
                    delta_keff,
                ]
            )
            + " |"
        )

    if completed_deltas:
        max_abs_delta = max(completed_deltas)
        conclusion = (
            f"Completed cases: {len(completed_deltas)}/5. "
            f"Maximum absolute delta keff = {max_abs_delta:.5f}."
        )
    else:
        conclusion = "Pending MCNP completion."

    lines = [
        "# Centrifuge Unit Cell OpenMC/MCNP Comparison",
        "",
        "## Objective",
        "",
        "Compare the canonical `centrifuge-unit-cell` OpenMC model against manual MCNP",
        "case files built from the same reflective unit-cell geometry for fill heights",
        "from 10 cm through 50 cm.",
        "",
        "## Structure",
        "",
        "| Path | Purpose |",
        "|------|---------|",
        "| `study.yaml` | OpenMC sweep definition |",
        "| `openmc/runs/` | Raw OpenMC run outputs |",
        "| `mcnp/fill_*/` | Manual MCNP case directories and outputs |",
        "| `results.csv` | Combined solver results with a `solver` column |",
        "| `report.md` | Human-readable comparison summary |",
        "",
        "## Sweep Matrix",
        "",
        "| Case | Fill plane | Fill fraction | MCNP source z | Notes |",
        "|------|------------|---------------|---------------|-------|",
        "| `fill_10` | `surface 9 = pz 10` | `0.1` | `5` | Keeps source inside the fuel region |",
        "| `fill_20` | `surface 9 = pz 20` | `0.2` | `10` | Matches the canonical deck |",
        "| `fill_30` | `surface 9 = pz 30` | `0.3` | `10` | Literal deck copy plus fill change |",
        "| `fill_40` | `surface 9 = pz 40` | `0.4` | `10` | Literal deck copy plus fill change |",
        "| `fill_50` | `surface 9 = pz 50` | `0.5` | `10` | Literal deck copy plus fill change |",
        "",
        "## Comparison Summary",
        "",
        "| Fill z (cm) | MCNP keff | OpenMC keff | MCNP std | OpenMC std | Delta keff |",
        "|-------------|-----------|-------------|----------|------------|------------|",
        *comparison_lines,
        "",
        "## Conclusion",
        "",
        conclusion,
        "",
    ]

    REPORT_PATH.write_text("\n".join(lines), encoding="ascii")


def main() -> None:
    rows = update_results()
    update_report(rows)


if __name__ == "__main__":
    main()
