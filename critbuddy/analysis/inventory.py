"""
Inventory helpers that combine resolved geometry volume with UO2F2 chemistry.
"""

from __future__ import annotations

from dataclasses import dataclass

from critbuddy.core.materials.uo2f2_physics import uo2f2_stoichiometry


@dataclass(frozen=True)
class UF6Inventory:
    """Resolved UF6 fill inventory for one geometry state."""

    total_volume_cm3: float
    total_volume_l: float
    fill_fraction: float
    filled_volume_cm3: float
    filled_volume_l: float
    bulk_density_g_cm3: float
    uf6_mass_kg: float


@dataclass(frozen=True)
class UO2F2Inventory:
    """Resolved UO2F2 fill inventory for one geometry/chemistry state."""

    total_volume_cm3: float
    total_volume_l: float
    fill_fraction: float
    filled_volume_cm3: float
    filled_volume_l: float
    bulk_density_g_cm3: float
    uo2f2_component_density_g_cm3: float
    h2o_component_density_g_cm3: float
    wet_solution_mass_kg: float
    uo2f2_mass_kg: float
    water_mass_kg: float
    enrichment_pct: float
    h_to_u: float


def compute_uf6_inventory(
    *,
    total_volume_cm3: float,
    fill_fraction: float,
    density_g_cm3: float = 5.09,
) -> UF6Inventory:
    """Convert a fill fraction and total fillable volume into UF6 inventory."""
    if total_volume_cm3 <= 0.0:
        raise ValueError("total_volume_cm3 must be positive")
    if not 0.0 <= fill_fraction <= 1.5:
        raise ValueError("fill_fraction must be between 0.0 and 1.5")
    if density_g_cm3 <= 0.0:
        raise ValueError("density_g_cm3 must be positive")

    filled_volume_cm3 = total_volume_cm3 * fill_fraction

    return UF6Inventory(
        total_volume_cm3=total_volume_cm3,
        total_volume_l=total_volume_cm3 / 1000.0,
        fill_fraction=fill_fraction,
        filled_volume_cm3=filled_volume_cm3,
        filled_volume_l=filled_volume_cm3 / 1000.0,
        bulk_density_g_cm3=density_g_cm3,
        uf6_mass_kg=density_g_cm3 * filled_volume_cm3 / 1000.0,
    )


def compute_uo2f2_inventory(
    *,
    total_volume_cm3: float,
    fill_fraction: float,
    h_to_u: float,
    enrichment_pct: float,
) -> UO2F2Inventory:
    """Convert a fill fraction and total fillable volume into UO2F2 inventory."""
    if total_volume_cm3 <= 0.0:
        raise ValueError("total_volume_cm3 must be positive")
    if not 0.0 <= fill_fraction <= 1.5:
        raise ValueError("fill_fraction must be between 0.0 and 1.5")

    stoich = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment_pct)
    filled_volume_cm3 = total_volume_cm3 * fill_fraction

    return UO2F2Inventory(
        total_volume_cm3=total_volume_cm3,
        total_volume_l=total_volume_cm3 / 1000.0,
        fill_fraction=fill_fraction,
        filled_volume_cm3=filled_volume_cm3,
        filled_volume_l=filled_volume_cm3 / 1000.0,
        bulk_density_g_cm3=stoich.density_g_cm3,
        uo2f2_component_density_g_cm3=stoich.uo2f2_component_density_g_cm3,
        h2o_component_density_g_cm3=stoich.h2o_component_density_g_cm3,
        wet_solution_mass_kg=stoich.density_g_cm3 * filled_volume_cm3 / 1000.0,
        uo2f2_mass_kg=stoich.uo2f2_component_density_g_cm3 * filled_volume_cm3 / 1000.0,
        water_mass_kg=stoich.h2o_component_density_g_cm3 * filled_volume_cm3 / 1000.0,
        enrichment_pct=enrichment_pct,
        h_to_u=h_to_u,
    )
