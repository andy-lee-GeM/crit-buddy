"""
OpenMC material builders and package-facing material helpers.
"""

from __future__ import annotations

import openmc
from critbuddy.core.materials.material_specs import (
    MATERIAL_ALIASES,
    MATERIAL_DENSITIES,
    STATIC_MATERIAL_SPECS,
    MaterialSpec,
)
from critbuddy.core.materials.uo2f2_physics import uo2f2_stoichiometry, uo2f2_density


def _is_nuclide_species(name: str) -> bool:
    """Return True when the species key names a specific nuclide."""
    return any(char.isdigit() for char in name)


def _build_material_from_spec(spec: MaterialSpec) -> openmc.Material:
    """Build an OpenMC material from a static spec."""
    mat = openmc.Material(name=spec.name)
    mat.set_density("g/cm3", spec.density_g_cm3)

    for species, fraction in spec.components.items():
        if _is_nuclide_species(species):
            mat.add_nuclide(species, fraction, percent_type=spec.fraction_basis)
        else:
            mat.add_element(species, fraction, percent_type=spec.fraction_basis)

    for sab_name in spec.sab:
        mat.add_s_alpha_beta(sab_name)

    return mat


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
    return _build_material_from_spec(STATIC_MATERIAL_SPECS["aluminum"])


def stainless_steel_304() -> openmc.Material:
    """Create SS304 using the explicit isotope mix used by the Andy MCNP deck."""
    return _build_material_from_spec(STATIC_MATERIAL_SPECS["stainless_steel_304"])


def stainless_steel_316() -> openmc.Material:
    """Create simplified nominal stainless steel 316."""
    return _build_material_from_spec(STATIC_MATERIAL_SPECS["stainless_steel_316"])


def concrete() -> openmc.Material:
    """Create ordinary concrete using weight fractions."""
    return _build_material_from_spec(STATIC_MATERIAL_SPECS["concrete_ordinary"])


def concrete_ordinary() -> openmc.Material:
    """Compatibility wrapper for ordinary concrete."""
    return concrete()


def water(density_g_cm3: float = 1.0) -> openmc.Material:
    """Create water with thermal scattering."""
    mat = _build_material_from_spec(STATIC_MATERIAL_SPECS["water"])
    mat.set_density("g/cm3", density_g_cm3)
    return mat


def air_dry() -> openmc.Material:
    """Create dry air at STP using cross-section-safe isotopes."""
    return _build_material_from_spec(STATIC_MATERIAL_SPECS["air_dry"])


def humid_air() -> openmc.Material:
    """Create a conservative humid air composition."""
    return _build_material_from_spec(STATIC_MATERIAL_SPECS["humid_air"])


def centrifuge_air() -> openmc.Material:
    """Create the legacy centrifuge MCNP air card for parity work."""
    mat = openmc.Material(name="Air")
    mat.set_density("atom/b-cm", 3.3e-02)
    mat.add_nuclide("N14", 3.9e-05, percent_type="ao")
    mat.add_nuclide("O16", 1.05e-05, percent_type="ao")
    mat.add_nuclide("Ar40", 2.4e-04, percent_type="ao")
    mat.add_nuclide("H1", 1.1e-06, percent_type="ao")
    return mat


def vacuum() -> openmc.Material:
    """Create a near-zero density material for evacuated regions."""
    return _build_material_from_spec(STATIC_MATERIAL_SPECS["vacuum"])


def void() -> openmc.Material:
    """Create very low-density air for headspace/void modeling."""
    return _build_material_from_spec(STATIC_MATERIAL_SPECS["void"])


def uf6(enrichment_pct: float, density: float = 5.09) -> openmc.Material:
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


def uo2f2(
    enrichment_pct: float,
    h_to_u: float,
    density: float,
) -> openmc.Material:
    """Create UO2F2 with an explicit H/U ratio."""
    u235_frac, u238_frac = _uranium_fractions(enrichment_pct)
    stoich = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment_pct)
    mat = openmc.Material(name="UO2F2")
    mat.set_density("g/cm3", density)
    mat.add_nuclide("U235", u235_frac, percent_type="ao")
    mat.add_nuclide("U238", u238_frac, percent_type="ao")
    if stoich.hydrogen_atoms_per_u > 0.0:
        mat.add_nuclide("H1", stoich.hydrogen_atoms_per_u, percent_type="ao")
        mat.add_s_alpha_beta("c_H_in_H2O")
    mat.add_nuclide("O16", stoich.oxygen_atoms_per_u, percent_type="ao")
    mat.add_nuclide("F19", stoich.fluorine_atoms_per_u, percent_type="ao")
    return mat


def create_fissile_material(
    fissile_material: str,
    enrichment_pct: float,
    fissile_density: float | None = None,
    h_to_u: float | None = None,
) -> openmc.Material:
    """Create a fissile material selected by template-facing name."""
    key = fissile_material.lower()

    if key == "uf6":
        density = 5.09 if fissile_density is None else fissile_density
        return uf6(enrichment_pct, density=density)
    if key == "uo2f2":
        if h_to_u is None:
            raise ValueError("UO2F2 material creation requires an explicit h_to_u")
        density = fissile_density
        if density is None:
            density = uo2f2_density(h_to_u, enrichment_pct=enrichment_pct)
        return uo2f2(enrichment_pct, h_to_u=h_to_u, density=density)

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


def create_uf6(enrichment_pct: float, density: float = 5.09) -> openmc.Material:
    """Compatibility wrapper for the normalized uf6 constructor."""
    return uf6(enrichment_pct, density=density)


def create_vacuum() -> openmc.Material:
    """Compatibility wrapper for templates that import create_vacuum."""
    return vacuum()


MATERIAL_LIBRARY = {
    "aluminum": aluminum,
    "stainless_steel_304": stainless_steel_304,
    "stainless_steel_316": stainless_steel_316,
    "water": water,
    "concrete_ordinary": concrete_ordinary,
    "air_dry": air_dry,
    "humid_air": humid_air,
    "centrifuge_air": centrifuge_air,
    "void": void,
    "vacuum": vacuum,
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
    normalized = name.strip()

    if normalized.startswith("UO2F2"):
        return MATERIAL_COLORS["UO2F2"]
    if normalized.startswith("UF6"):
        return MATERIAL_COLORS["UF6"]

    lower_name = normalized.lower()
    if "fuel" in lower_name:
        return MATERIAL_COLORS["UO2F2"]
    if "water" in lower_name:
        return MATERIAL_COLORS["Water"]
    if "air" in lower_name:
        return MATERIAL_COLORS["Air"]
    if "wall" in lower_name or "steel" in lower_name:
        return MATERIAL_COLORS["Stainless_Steel_316"]

    return MATERIAL_COLORS.get(normalized, (200, 200, 200))


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
