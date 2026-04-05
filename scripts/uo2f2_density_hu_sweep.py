#!/usr/bin/env python3
"""Export UO2F2 density traceability tables for requested H/U values."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from critbuddy.core.materials.uo2f2_physics import UO2F2_MODEL, uo2f2_stoichiometry


def _parse_float_list(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def _frange(start: float, stop: float, step: float) -> list[float]:
    if step <= 0.0:
        raise ValueError("--h-step must be positive")

    values: list[float] = []
    current = start
    while current <= stop + 1.0e-9:
        values.append(round(current, 10))
        current += step
    return values


def _resolve_h_values(args: argparse.Namespace) -> list[float]:
    if args.h_values:
        return args.h_values
    if args.h_start is None or args.h_stop is None or args.h_step is None:
        raise ValueError("Provide either --h-values or the full --h-start/--h-stop/--h-step range")
    return _frange(args.h_start, args.h_stop, args.h_step)


def _density_basis_region(h_to_u: float) -> str:
    if h_to_u < UO2F2_MODEL.h_over_u_transition:
        return "hydrated_salt_linear_fit"
    return "appendix_a_volume_relation"


def _build_rows(enrichment: float, h_values: list[float]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for h_to_u in h_values:
        stoich = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment)
        rows.append(
            {
                "enrichment_wt_pct": enrichment,
                "h_to_u": h_to_u,
                "uranium_density_g_cm3": stoich.uranium_density_g_cm3,
                "bulk_density_g_cm3": stoich.density_g_cm3,
                "uo2f2_component_density_g_cm3": stoich.uo2f2_component_density_g_cm3,
                "h2o_component_density_g_cm3": stoich.h2o_component_density_g_cm3,
                "water_weight_fraction": stoich.water_weight_fraction,
                "water_moles_per_u": stoich.water_moles_per_u,
                "density_basis_region": _density_basis_region(h_to_u),
            }
        )
    return rows


def _write_csv(rows: list[dict[str, object]], output_path: Path | None) -> None:
    fieldnames = list(rows[0].keys()) if rows else []

    if output_path is None:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown(rows: list[dict[str, object]], output_path: Path | None) -> None:
    headers = [
        "enrichment_wt_pct",
        "h_to_u",
        "uranium_density_g_cm3",
        "bulk_density_g_cm3",
        "uo2f2_component_density_g_cm3",
        "h2o_component_density_g_cm3",
        "water_weight_fraction",
        "water_moles_per_u",
        "density_basis_region",
    ]
    lines = [
        "| Enrichment (wt%) | H/U | U density (g/cm3) | Bulk density (g/cm3) | UO2F2 component (g/cm3) | H2O component (g/cm3) | Water wt frac | Water mol/U | Density basis region |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"{float(row['enrichment_wt_pct']):.2f}",
                    f"{float(row['h_to_u']):.4f}",
                    f"{float(row['uranium_density_g_cm3']):.8f}",
                    f"{float(row['bulk_density_g_cm3']):.8f}",
                    f"{float(row['uo2f2_component_density_g_cm3']):.8f}",
                    f"{float(row['h2o_component_density_g_cm3']):.8f}",
                    f"{float(row['water_weight_fraction']):.8f}",
                    f"{float(row['water_moles_per_u']):.8f}",
                    str(row["density_basis_region"]),
                ]
            )
            + " |"
        )

    content = "\n".join(lines) + "\n"
    if output_path is None:
        sys.stdout.write(content)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export UO2F2 density tables for requested H/U values.")
    parser.add_argument("--enrichment", type=float, required=True, help="U-235 enrichment in weight percent.")
    parser.add_argument("--h-values", type=_parse_float_list, help="Comma-separated H/U values.")
    parser.add_argument("--h-start", type=float, help="H/U range start.")
    parser.add_argument("--h-stop", type=float, help="H/U range stop.")
    parser.add_argument("--h-step", type=float, help="H/U range step.")
    parser.add_argument("--format", choices=["csv", "markdown"], default="csv")
    parser.add_argument("--output", type=Path, help="Optional output path.")
    args = parser.parse_args()

    h_values = _resolve_h_values(args)
    rows = _build_rows(args.enrichment, h_values)

    if args.format == "csv":
        _write_csv(rows, args.output)
    else:
        _write_markdown(rows, args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
