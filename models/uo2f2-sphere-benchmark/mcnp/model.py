"""MCNP render helpers for uo2f2-sphere-benchmark."""

from __future__ import annotations

from critbuddy.core.materials.builders import uo2f2, water
from critbuddy.core.materials.mcnp_conversion import MCNPMaterial


def _format_material_card(mat_num: int, material: MCNPMaterial) -> str:
    """Render one MCNP material card using normalized atom fractions."""
    lines = []
    first, *rest = material.nuclides
    lines.append(f"m{mat_num} {first.zaid} {first.atom_fraction:.8e}")
    for nuc in rest:
        lines.append(f"     {nuc.zaid} {nuc.atom_fraction:.8e}")
    return "\n".join(lines)


def _thermal_card(mat_num: int, material_name: str) -> str:
    """Return thermal scattering card when the material contains bound water hydrogen."""
    if material_name.lower() in {"uo2f2", "water"}:
        return f"mt{mat_num} lwtr.01t"
    return ""


def build_render_params(params: dict) -> dict:
    """Build MCNP-specific template parameters from shared model params."""
    fuel = uo2f2(
        enrichment_pct=params["ENRICHMENT_PCT"],
        h_to_u=params["H_TO_U"],
        density=params["UO2F2_DENSITY_G_CM3"],
    )
    reflector = water(density_g_cm3=params["REFLECTOR_DENSITY_G_CM3"])

    fuel_mcnp = MCNPMaterial.from_openmc(fuel, xs_suffix="80c")
    reflector_mcnp = MCNPMaterial.from_openmc(reflector, xs_suffix="80c")

    outer_surface_prefix = "*" if str(params["OUTER_BOUNDARY_TYPE"]).lower() == "reflective" else ""

    return {
        "FUEL_CELL_DENSITY": f"{fuel_mcnp.cell_density_g_cm3:.8f}",
        "REFLECTOR_CELL_DENSITY": f"{reflector_mcnp.cell_density_g_cm3:.8f}",
        "OUTER_SURFACE_CARD": (
            f"{outer_surface_prefix}2 so {params['OUTER_RADIUS_CM']:.6f}"
            "  $ outer reflector radius [cm]"
        ),
        "FUEL_MATERIAL_CARD": _format_material_card(1, fuel_mcnp),
        "FUEL_THERMAL_CARD": _thermal_card(1, fuel_mcnp.name),
        "REFLECTOR_MATERIAL_CARD": _format_material_card(2, reflector_mcnp),
        "REFLECTOR_THERMAL_CARD": _thermal_card(2, reflector_mcnp.name),
    }
