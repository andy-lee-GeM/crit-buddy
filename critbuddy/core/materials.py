"""
OpenMC material factory library used across crit-buddy templates.

The module is intentionally OpenMC-only. Common engineering materials are
represented as element-based weight-fraction factories, while chemistry-driven
materials remain parameterized builders.
"""

from __future__ import annotations

import openmc
from .uo2f2_physics import (
    UO2F2Stoichiometry,
    uo2f2_density,
    uo2f2_stoichiometry,
)

def _uranium_fractions(enrichment_pct: float) -> tuple[float, float]:
    """Convert U-235 weight percent to uranium atom fractions."""
    m_u235 = 235.044
    m_u238 = 238.051

    w235 = enrichment_pct / 100.0
    w238 = 1.0 - w235

    moles_u235 = w235 / m_u235
    moles_u238 = w238 / m_u238
    total_moles = moles_u235 + moles_u238

    return moles_u235 / total_moles, moles_u238 / total_moles


def aluminum() -> openmc.Material:
    """Create pure aluminum."""
    mat = openmc.Material(name="Aluminum")
    mat.set_density("g/cm3", 2.70)
    mat.add_element("Al", 1.0, percent_type="wo")
    return mat


def stainless_steel_304() -> openmc.Material:
    """Create simplified nominal stainless steel 304."""
    mat = openmc.Material(name="Stainless_Steel_304")
    mat.set_density("g/cm3", 7.94)
    mat.add_element("Fe", 0.70, percent_type="wo")
    mat.add_element("Cr", 0.19, percent_type="wo")
    mat.add_element("Ni", 0.10, percent_type="wo")
    mat.add_element("Mn", 0.01, percent_type="wo")
    return mat


def stainless_steel_316() -> openmc.Material:
    """Create simplified nominal stainless steel 316."""
    mat = openmc.Material(name="Stainless_Steel_316")
    mat.set_density("g/cm3", 8.00)
    mat.add_element("Fe", 0.68, percent_type="wo")
    mat.add_element("Cr", 0.17, percent_type="wo")
    mat.add_element("Ni", 0.12, percent_type="wo")
    mat.add_element("Mo", 0.025, percent_type="wo")
    mat.add_element("Mn", 0.005, percent_type="wo")
    return mat


def concrete_ordinary() -> openmc.Material:
    """Create ordinary concrete using weight fractions."""
    mat = openmc.Material(name="Concrete")
    mat.set_density("g/cm3", 2.30)
    mat.add_element("H", 0.01, percent_type="wo")
    mat.add_element("O", 0.53, percent_type="wo")
    mat.add_element("Si", 0.34, percent_type="wo")
    mat.add_element("Ca", 0.04, percent_type="wo")
    mat.add_element("Al", 0.03, percent_type="wo")
    mat.add_element("Fe", 0.01, percent_type="wo")
    return mat


def water(density_g_cm3: float = 1.0) -> openmc.Material:
    """Create water with thermal scattering."""
    mat = openmc.Material(name="Water")
    mat.set_density("g/cm3", density_g_cm3)
    mat.add_nuclide("H1", 2.0, percent_type="ao")
    mat.add_nuclide("O16", 1.0, percent_type="ao")
    mat.add_s_alpha_beta("c_H_in_H2O")
    return mat


def air_dry() -> openmc.Material:
    """Create dry air at STP."""
    mat = openmc.Material(name="Air")
    mat.set_density("g/cm3", 0.001225)
    mat.add_element("N", 0.78, percent_type="ao")
    mat.add_element("O", 0.21, percent_type="ao")
    mat.add_element("Ar", 0.01, percent_type="ao")
    return mat


def humid_air() -> openmc.Material:
    """Create a conservative humid air composition."""
    mat = openmc.Material(name="Humid_Air")
    mat.set_density("g/cm3", 0.0011)
    mat.add_element("N", 0.702, percent_type="ao")
    mat.add_element("O", 0.223, percent_type="ao")
    mat.add_element("Ar", 0.004, percent_type="ao")
    mat.add_element("H", 0.071, percent_type="ao")
    return mat


def vacuum() -> openmc.Material:
    """Create a near-zero density material for evacuated regions."""
    mat = openmc.Material(name="Vacuum")
    mat.set_density("g/cm3", 1.0e-10)
    mat.add_nuclide("N14", 1.0, percent_type="ao")
    return mat


def void() -> openmc.Material:
    """Create very low-density air for headspace/void modeling."""
    mat = openmc.Material(name="Void")
    mat.set_density("g/cm3", 0.0001)
    mat.add_element("N", 0.78, percent_type="ao")
    mat.add_element("O", 0.21, percent_type="ao")
    mat.add_element("Ar", 0.01, percent_type="ao")
    return mat


def create_uf6(enrichment_pct: float, density: float = 5.09) -> openmc.Material:
    """Create UF6 using explicit uranium isotopics."""
    u235_frac, u238_frac = _uranium_fractions(enrichment_pct)
    mat = openmc.Material(name="UF6")
    mat.set_density("g/cm3", density)
    mat.add_nuclide("U235", u235_frac, percent_type="ao")
    mat.add_nuclide("U238", u238_frac, percent_type="ao")
    mat.add_nuclide("F19", 6.0, percent_type="ao")
    return mat


def create_hf() -> openmc.Material:
    """Create pure hydrogen fluoride."""
    mat = openmc.Material(name="HF")
    mat.set_density("g/cm3", 1.0)
    mat.add_nuclide("H1", 1.0, percent_type="ao")
    mat.add_nuclide("F19", 1.0, percent_type="ao")
    return mat


def create_uo2f2(
    enrichment_pct: float,
    h_to_u: float = 0.0,
) -> openmc.Material:
    """Create uranyl fluoride for OpenMC from enrichment and H/U."""
    u235_frac, u238_frac = _uranium_fractions(enrichment_pct)
    stoich = uo2f2_stoichiometry(h_to_u, enrichment_pct=enrichment_pct)

    composition = {
        "U235": u235_frac,
        "U238": u238_frac,
        "O16": stoich.oxygen_atoms_per_u,
        "F19": stoich.fluorine_atoms_per_u,
    }
    if stoich.hydrogen_atoms_per_u > 0.0:
        composition["H1"] = stoich.hydrogen_atoms_per_u

    mat = openmc.Material(name=f"UO2F2_H{h_to_u:g}" if h_to_u > 0 else "UO2F2")
    mat.set_density("g/cm3", stoich.density_g_cm3)
    for nuclide, amount in composition.items():
        mat.add_nuclide(nuclide, amount, percent_type="ao")
    if stoich.hydrogen_atoms_per_u > 0.0:
        mat.add_s_alpha_beta("c_H_in_H2O")
    return mat


def create_uf6_with_hf(
    enrichment_pct: float,
    density: float = 5.09,
    hf_wt_pct: float = 0.5,
) -> openmc.Material:
    """Create UF6 with an HF impurity specified in weight percent."""
    uf6 = create_uf6(enrichment_pct, density)
    hf = create_hf()

    uf6_wt_frac = (100.0 - hf_wt_pct) / 100.0
    hf_wt_frac = hf_wt_pct / 100.0

    mat = openmc.Material.mix_materials(
        [uf6, hf],
        [uf6_wt_frac, hf_wt_frac],
        percent_type="wo",
        name="UF6_HF",
    )
    mat.set_density("g/cm3", density)
    return mat


def create_fissile_material(
    fissile_material: str,
    enrichment_pct: float,
    fissile_density: float | None = None,
    h_to_u: float = 0.0,
) -> openmc.Material:
    """Create a fissile material selected by template-facing name."""
    key = fissile_material.lower()

    if key == "uf6":
        density = 5.09 if fissile_density is None else fissile_density
        return create_uf6(enrichment_pct, density=density)
    if key == "uo2f2":
        if fissile_density is not None:
            raise ValueError("UO2F2 density is derived from enrichment and H/U and cannot be overridden")
        return create_uo2f2(enrichment_pct, h_to_u=h_to_u)

    raise ValueError(f"Unsupported fissile_material '{fissile_material}'")


def create_environment_material(
    environment_material: str,
    environment_density: float | None = None,
) -> openmc.Material:
    """Create an environment material with an optional density override."""
    mat = get_material(environment_material)
    if environment_density is not None:
        mat.set_density("g/cm3", environment_density)
    return mat


MATERIAL_LIBRARY = {
    "aluminum": aluminum,
    "stainless_steel_304": stainless_steel_304,
    "stainless_steel_316": stainless_steel_316,
    "water": water,
    "concrete_ordinary": concrete_ordinary,
    "air_dry": air_dry,
    "humid_air": humid_air,
    "void": void,
    "vacuum": vacuum,
}


MATERIAL_DENSITIES = {
    "aluminum": 2.70,
    "stainless_steel_304": 7.94,
    "stainless_steel_316": 8.00,
    "water": 1.0,
    "concrete_ordinary": 2.30,
    "air_dry": 0.001225,
    "humid_air": 0.0011,
    "void": 0.0001,
    "vacuum": 1.0e-10,
}


MATERIAL_ALIASES = {
    "air": "air_dry",
    "aluminum_6061": "aluminum",
    "concrete": "concrete_ordinary",
    "ss304": "stainless_steel_304",
    "steel": "stainless_steel_316",
}


MATERIAL_REGISTRY = MATERIAL_LIBRARY


MATERIAL_COLORS = {
    "Air": (173, 216, 230),
    "Aluminum": (147, 112, 219),
    "Concrete": (188, 143, 143),
    "Humid_Air": (173, 216, 230),
    "Stainless_Steel_304": (70, 70, 70),
    "Stainless_Steel_316": (50, 50, 50),
    "UF6": (0, 200, 0),
    "UF6_HF": (0, 200, 0),
    "UO2F2": (0, 180, 0),
    "Vacuum": (255, 230, 230),
    "Void": (255, 255, 255),
    "Water": (135, 206, 250),
}


def _resolve_material_name(name: str) -> str:
    key = name.lower()
    if key in MATERIAL_LIBRARY:
        return key
    if key in MATERIAL_ALIASES:
        return MATERIAL_ALIASES[key]
    available = sorted(set(MATERIAL_LIBRARY) | set(MATERIAL_ALIASES))
    raise ValueError(f"Unknown material: '{name}'. Available: {available}")


def get_material_color(name: str) -> tuple[int, int, int]:
    """Get RGB color tuple for a material by name."""
    if name.startswith("UO2F2"):
        return MATERIAL_COLORS["UO2F2"]
    return MATERIAL_COLORS.get(name, (200, 200, 200))


def get_color_mapping(materials) -> dict:
    """Build color mapping dict for OpenMC plots from a Materials object."""
    return {mat: get_material_color(mat.name) for mat in materials}


def get_color_legend(materials) -> dict:
    """Build color legend dict for plot annotations."""
    return {mat.name: get_material_color(mat.name) for mat in materials}


def get_material(name: str, solver: str = "openmc") -> openmc.Material:
    """Get a named OpenMC material from the shared library."""
    if solver != "openmc":
        raise ValueError("critbuddy.core.materials is OpenMC-only; solver must be 'openmc'")

    canonical_name = _resolve_material_name(name)
    return MATERIAL_LIBRARY[canonical_name]()


def get_density(name: str) -> float:
    """Get default density by material name."""
    canonical_name = _resolve_material_name(name)
    return MATERIAL_DENSITIES[canonical_name]
