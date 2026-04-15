#!/usr/bin/env python3
"""Audit frozen certification fuel densities against the current shared UO2F2 basis."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CERTIFICATIONS_ROOT = ROOT / "certifications"
sys.path.insert(0, str(ROOT))

from critbuddy.core.config import ExperimentConfig, expand_sweeps
from critbuddy.core.materials.uo2f2_physics import uo2f2_density
from critbuddy.core.template_loader import load_model_class


@dataclass
class FuelMaterial:
    density_units: str
    density_g_cm3: float
    has_hydrogen: bool


@dataclass
class AuditRow:
    certification: str
    model: str
    case: str
    density_mode: str
    h_to_u: float
    xml_density_g_cm3: float
    case_density_g_cm3: float
    current_density_g_cm3: float
    delta_current_g_cm3: float
    verdict: str
    note: str


def _discover_certifications(explicit_paths: list[str]) -> list[Path]:
    if explicit_paths:
        return [Path(path).resolve() for path in explicit_paths]

    discovered: list[Path] = []
    for model_dir in sorted(CERTIFICATIONS_ROOT.iterdir()):
        if not model_dir.is_dir():
            continue
        for cert_dir in sorted(model_dir.iterdir()):
            if (cert_dir / "openmc" / "study.yaml").exists():
                discovered.append(cert_dir)
    return discovered


def _load_fuel_material(materials_path: Path) -> FuelMaterial:
    root = ET.parse(materials_path).getroot()
    for material in root.findall("material"):
        if material.get("name") != "Fuel":
            continue
        density = material.find("density")
        if density is None:
            raise ValueError(f"Fuel material in {materials_path} has no density block")
        density_units = density.get("units", "")
        density_value = float(density.get("value", "nan"))
        has_hydrogen = any(
            nuclide.get("name") == "H1"
            for nuclide in material.findall("nuclide")
        )
        return FuelMaterial(
            density_units=density_units,
            density_g_cm3=density_value,
            has_hydrogen=has_hydrogen,
        )
    raise ValueError(f"No Fuel material found in {materials_path}")


def _audit_certification(cert_dir: Path, tolerance: float) -> list[AuditRow]:
    study_path = cert_dir / "openmc" / "study.yaml"
    config = ExperimentConfig.from_file(study_path)
    model_name = config.definition_name
    template = load_model_class(model_name)
    user_params = template.apply_defaults(config.user_params)
    cases = [
        (label, params, template.derive_params(params))
        for label, params in expand_sweeps(user_params)
    ]

    rows: list[AuditRow] = []
    for label, params, derived in cases:
        materials_path = cert_dir / "openmc" / "cases" / label / "materials.xml"
        fuel = _load_fuel_material(materials_path)

        enrichment_pct = float(derived["ENRICHMENT_PCT"])
        h_to_u = float(derived.get("H_TO_U", 0.0))
        current_density = uo2f2_density(h_to_u=h_to_u, enrichment_pct=enrichment_pct)
        case_density = float(derived.get("UO2F2_DENSITY_G_CM3", current_density))
        density_mode = str(derived.get("UO2F2_DENSITY_MODE", "shared_fissile_builder"))

        note_parts: list[str] = []
        if fuel.density_units != "g/cm3":
            verdict = "unexpected_units"
            note_parts.append(f"Fuel density units are {fuel.density_units!r}")
        elif abs(fuel.density_g_cm3 - case_density) > tolerance:
            verdict = "artifact_mismatch"
            note_parts.append("materials.xml density does not match the resolved case density")
        elif density_mode == "legacy_explicit_density":
            verdict = "legacy_explicit_basis"
            note_parts.append("frozen case replays a legacy explicit density override")
        else:
            verdict = "current_shared_basis"

        if h_to_u > 0.0 and not fuel.has_hydrogen:
            note_parts.append("H/U > 0 but the frozen fuel material has no hydrogen nuclide")
        if h_to_u == 0.0 and fuel.has_hydrogen:
            note_parts.append("H/U = 0 but the frozen fuel material includes hydrogen")

        rows.append(
            AuditRow(
                certification=str(cert_dir.relative_to(ROOT)),
                model=model_name,
                case=label,
                density_mode=density_mode,
                h_to_u=h_to_u,
                xml_density_g_cm3=fuel.density_g_cm3,
                case_density_g_cm3=case_density,
                current_density_g_cm3=current_density,
                delta_current_g_cm3=fuel.density_g_cm3 - current_density,
                verdict=verdict,
                note="; ".join(note_parts),
            )
        )

    return rows


def _format_table(rows: list[AuditRow]) -> str:
    headers = [
        "certification",
        "case",
        "mode",
        "h/u",
        "xml_rho",
        "case_rho",
        "current_rho",
        "delta_current",
        "verdict",
    ]
    raw_rows = [
        [
            row.certification,
            row.case,
            row.density_mode,
            f"{row.h_to_u:.3f}",
            f"{row.xml_density_g_cm3:.6f}",
            f"{row.case_density_g_cm3:.6f}",
            f"{row.current_density_g_cm3:.6f}",
            f"{row.delta_current_g_cm3:+.6f}",
            row.verdict,
        ]
        for row in rows
    ]

    widths = [
        max(len(header), *(len(values[idx]) for values in raw_rows))
        for idx, header in enumerate(headers)
    ]

    lines = [
        "  ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers)),
        "  ".join("-" * widths[idx] for idx in range(len(headers))),
    ]
    for values in raw_rows:
        lines.append(
            "  ".join(value.ljust(widths[idx]) for idx, value in enumerate(values))
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit certification fuel densities against the current shared UO2F2 basis."
    )
    parser.add_argument(
        "certifications",
        nargs="*",
        help="Optional certification directories to audit. Defaults to all under certifications/.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1.0e-6,
        help="Absolute tolerance used when comparing the frozen materials.xml density to the resolved case density.",
    )
    args = parser.parse_args()

    certification_dirs = _discover_certifications(args.certifications)
    if not certification_dirs:
        print("No certification directories found.", file=sys.stderr)
        return 1

    rows: list[AuditRow] = []
    for cert_dir in certification_dirs:
        rows.extend(_audit_certification(cert_dir, tolerance=args.tolerance))

    print(_format_table(rows))

    notes = [row for row in rows if row.note]
    if notes:
        print("\nNotes:")
        for row in notes:
            print(f"- {row.certification} {row.case}: {row.note}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
