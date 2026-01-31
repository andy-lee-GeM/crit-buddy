"""
Shared material definitions for criticality safety analyses.

Provides material definitions for both OpenMC and MCNP solvers.
This ensures consistent material physics across all templates and solvers.

Usage (OpenMC):
    from critbuddy.core.materials import create_uf6, create_aluminum, create_water
    m1 = create_uf6(enrichment_pct=20.0, density=5.09)

Usage (MCNP):
    from critbuddy.core.materials import mcnp_uf6, mcnp_aluminum, mcnp_water
    materials_block = mcnp_uf6(1, 20.0, 5.09) + mcnp_aluminum(2) + mcnp_water(3)

Usage (Registry - for enum-based material selection):
    from critbuddy.core.materials import get_material, get_density
    wall = get_material("aluminum", solver="openmc")
    rho = get_density("aluminum")
"""

import openmc


# =============================================================================
# SHARED CALCULATIONS
# =============================================================================

def _uranium_fractions(enrichment_pct: float) -> tuple[float, float]:
    """
    Convert U-235 weight percent to atom fractions.

    Example:
        >>> _uranium_fractions(5.0)
        (0.0506, 0.9494)  # 5 wt% → ~5.06 atom%
    """
    M_U235 = 235.044  # atomic mass of U-235
    M_U238 = 238.051  # atomic mass of U-238

    # Convert percent to fraction
    w235 = enrichment_pct / 100.0  # weight fraction U-235
    w238 = 1.0 - w235               # weight fraction U-238

    # Convert weight fractions to moles (proportional to atoms)
    moles_u235 = w235 / M_U235
    moles_u238 = w238 / M_U238
    total_moles = moles_u235 + moles_u238

    # Atom fractions
    u235_atom_frac = moles_u235 / total_moles
    u238_atom_frac = moles_u238 / total_moles

    return u235_atom_frac, u238_atom_frac


# =============================================================================
# OPENMC MATERIALS
# =============================================================================
def create_uf6(enrichment_pct: float, density: float = 5.09) -> openmc.Material:
    """Create UF6 material for OpenMC using explicit U-235/U-238 nuclides."""
    u235_frac, u238_frac = _uranium_fractions(enrichment_pct)

    uf6 = openmc.Material(name="UF6")
    uf6.set_density(units="g/cm3", density=density)
    uf6.add_nuclide(nuclide="U235", percent=u235_frac, percent_type="ao")
    uf6.add_nuclide(nuclide="U238", percent=u238_frac, percent_type="ao")
    uf6.add_nuclide(nuclide="F19", percent=6.0, percent_type="ao")
    return uf6


def create_aluminum() -> openmc.Material:
    """Create aluminum for OpenMC."""
    al = openmc.Material(name="Aluminum")
    al.set_density("g/cm3", 2.70)
    al.add_nuclide("Al27", 1.0)
    return al


def create_steel() -> openmc.Material:
    """Create stainless steel 316 for OpenMC."""
    steel = openmc.Material(name="Steel")
    steel.set_density("g/cm3", 8.0)
    steel.add_nuclide("Fe56", 0.68)
    steel.add_nuclide("Cr52", 0.17)
    steel.add_nuclide("Ni58", 0.12)
    steel.add_nuclide("Mo96", 0.025)
    steel.add_nuclide("Mn55", 0.005)
    return steel


def create_water() -> openmc.Material:
    """Create water with thermal scattering for OpenMC."""
    water = openmc.Material(name="Water")
    water.set_density("g/cm3", 1.0)
    water.add_nuclide("H1", 2.0)
    water.add_nuclide("O16", 1.0)
    water.add_s_alpha_beta("c_H_in_H2O")
    return water


def create_concrete() -> openmc.Material:
    """Create ordinary concrete for OpenMC (simplified composition)."""
    concrete = openmc.Material(name="Concrete")
    concrete.set_density("g/cm3", 2.3)
    concrete.add_nuclide("H1", 0.01, "wo")
    concrete.add_nuclide("O16", 0.53, "wo")
    concrete.add_nuclide("Si28", 0.34, "wo")
    concrete.add_nuclide("Ca40", 0.04, "wo")
    concrete.add_nuclide("Al27", 0.03, "wo")
    concrete.add_nuclide("Fe56", 0.01, "wo")
    return concrete


def create_air() -> openmc.Material:
    """Create air for OpenMC."""
    air = openmc.Material(name="Air")
    air.set_density("g/cm3", 0.001225)
    air.add_nuclide("N14", 0.78)
    air.add_nuclide("O16", 1.0)
    air.add_nuclide("Ar40", 0.01)
    return air


def create_monel() -> openmc.Material:
    """
    Create Monel 400 alloy for OpenMC (5A/5B cylinder wall material).

    Monel 400 composition: ~67% Ni, ~30% Cu, ~2% Fe, ~1% Mn
    Density: 8.80 g/cm³
    """
    monel = openmc.Material(name="Monel")
    monel.set_density("g/cm3", 8.80)
    monel.add_nuclide("Ni58", 0.67, "wo")
    monel.add_nuclide("Cu63", 0.30, "wo")
    monel.add_nuclide("Fe56", 0.02, "wo")
    monel.add_nuclide("Mn55", 0.01, "wo")
    return monel


def create_carbon_steel() -> openmc.Material:
    """
    Create carbon steel for OpenMC (30B cylinder wall material).

    Per ORNL/TM-2021/2043, carbon steel at 7.82 g/cm³.
    Simplified composition: Fe with ~1% C.
    """
    cs = openmc.Material(name="Carbon_Steel")
    cs.set_density("g/cm3", 7.82)
    cs.add_nuclide("Fe56", 0.99, "wo")
    cs.add_nuclide("C0", 0.01, "wo")
    return cs


def create_ss304() -> openmc.Material:
    """
    Create stainless steel 304 for OpenMC (overpack material).

    Per ORNL/TM-2021/2043, SS304 at 7.94 g/cm³ for overpack.
    """
    ss304 = openmc.Material(name="SS304")
    ss304.set_density("g/cm3", 7.94)
    ss304.add_nuclide("Fe56", 0.70, "wo")
    ss304.add_nuclide("Cr52", 0.19, "wo")
    ss304.add_nuclide("Ni58", 0.10, "wo")
    ss304.add_nuclide("Mn55", 0.01, "wo")
    return ss304


def create_hf() -> openmc.Material:
    """Create pure HF (hydrogen fluoride) for OpenMC."""
    hf = openmc.Material(name="HF")
    hf.set_density("g/cm3", 1.0)  # Density not critical for mixing
    hf.add_nuclide("H1", 1.0, "ao")
    hf.add_nuclide("F19", 1.0, "ao")
    return hf


def create_uf6_with_hf(enrichment_pct: float, density: float = 5.09,
                        hf_wt_pct: float = 0.5) -> openmc.Material:
    """
    Create UF6 with HF impurity for OpenMC (30B cylinder contents).

    Per ORNL/TM-2021/2043: 99.5 wt% UF6 + 0.5 wt% HF.

    Uses mix_materials to combine pure UF6 and HF by weight fraction.

    Args:
        enrichment_pct: U-235 weight percent (of uranium only)
        density: Material density in g/cm3
        hf_wt_pct: HF weight percent (default 0.5 wt%)
    """
    uf6 = create_uf6(enrichment_pct, density)
    hf = create_hf()

    uf6_wt_frac = (100.0 - hf_wt_pct) / 100.0  # 0.995
    hf_wt_frac = hf_wt_pct / 100.0              # 0.005

    uf6_hf = openmc.Material.mix_materials(
        [uf6, hf],
        [uf6_wt_frac, hf_wt_frac],
        percent_type='wo',
        name='UF6_HF'
    )
    uf6_hf.set_density("g/cm3", density)

    return uf6_hf


# =============================================================================
# MCNP MATERIALS
# =============================================================================

def mcnp_uf6(mat_num: int, enrichment_pct: float, density: float = 5.09) -> str:
    """
    Generate MCNP material card for UF6.

    Args:
        mat_num: MCNP material number (e.g., 1)
        enrichment_pct: U-235 weight percent
        density: Material density in g/cm3

    Returns:
        MCNP material card text
    """
    u235_frac, u238_frac = _uranium_fractions(enrichment_pct)

    # UF6 has 7 atoms: 1 U + 6 F
    u235 = u235_frac / 7.0
    u238 = u238_frac / 7.0
    f19 = 6.0 / 7.0

    return f"""c Material {mat_num}: UF6 at {enrichment_pct:.2f} wt% U-235, {density:.4f} g/cm3
m{mat_num}   92235.80c  {u235:.6e}   $ U-235
     92238.80c  {u238:.6e}   $ U-238
     9019.80c   {f19:.6e}    $ F-19
"""


def mcnp_aluminum(mat_num: int) -> str:
    """Generate MCNP material card for aluminum."""
    return f"""c Material {mat_num}: Aluminum, 2.70 g/cm3
m{mat_num}   13027.80c  1.0   $ Al-27
"""


def mcnp_steel(mat_num: int) -> str:
    """Generate MCNP material card for stainless steel 316."""
    return f"""c Material {mat_num}: Stainless Steel 316, 8.0 g/cm3
m{mat_num}   26056.80c  0.68    $ Fe-56
     24052.80c  0.17    $ Cr-52
     28058.80c  0.12    $ Ni-58
     42096.80c  0.025   $ Mo-96
     25055.80c  0.005   $ Mn-55
"""


def mcnp_water(mat_num: int) -> str:
    """Generate MCNP material card for water with thermal scattering."""
    return f"""c Material {mat_num}: Water, 1.0 g/cm3
m{mat_num}   1001.80c   2.0   $ H-1
     8016.80c   1.0   $ O-16
mt{mat_num}  lwtr.20t         $ S(a,b) thermal scattering
"""


def mcnp_concrete(mat_num: int) -> str:
    """Generate MCNP material card for ordinary concrete."""
    return f"""c Material {mat_num}: Concrete, 2.3 g/cm3
m{mat_num}   1001.80c   0.01   $ H
     8016.80c   0.53   $ O
     14028.80c  0.34   $ Si
     20040.80c  0.04   $ Ca
     13027.80c  0.03   $ Al
     26056.80c  0.01   $ Fe
"""


def mcnp_air(mat_num: int) -> str:
    """Generate MCNP material card for air."""
    return f"""c Material {mat_num}: Air, 0.001225 g/cm3
m{mat_num}   7014.80c   0.78   $ N-14
     8016.80c   0.21   $ O-16
     18040.80c  0.01   $ Ar-40
"""


def mcnp_monel(mat_num: int) -> str:
    """Generate MCNP material card for Monel 400 alloy (5A/5B cylinders)."""
    return f"""c Material {mat_num}: Monel 400, 8.80 g/cm3
m{mat_num}   28058.80c  0.67   $ Ni-58
     29063.80c  0.30   $ Cu-63
     26056.80c  0.02   $ Fe-56
     25055.80c  0.01   $ Mn-55
"""


def mcnp_carbon_steel(mat_num: int) -> str:
    """Generate MCNP material card for carbon steel (30B cylinder)."""
    return f"""c Material {mat_num}: Carbon Steel, 7.82 g/cm3
m{mat_num}   26056.80c  0.99   $ Fe-56
     6000.80c   0.01   $ C-nat
"""


def mcnp_ss304(mat_num: int) -> str:
    """Generate MCNP material card for stainless steel 304 (overpack)."""
    return f"""c Material {mat_num}: Stainless Steel 304, 7.94 g/cm3
m{mat_num}   26056.80c  0.70   $ Fe-56
     24052.80c  0.19   $ Cr-52
     28058.80c  0.10   $ Ni-58
     25055.80c  0.01   $ Mn-55
"""



# =============================================================================
# MATERIAL REGISTRY (single source of truth for material properties)
# =============================================================================

MATERIAL_REGISTRY = {
    "aluminum": {
        "openmc": create_aluminum,
        "mcnp": mcnp_aluminum,
        "density": 2.70,
    },
    "steel": {
        "openmc": create_steel,
        "mcnp": mcnp_steel,
        "density": 8.0,
    },
    "water": {
        "openmc": create_water,
        "mcnp": mcnp_water,
        "density": 1.0,
    },
    "concrete": {
        "openmc": create_concrete,
        "mcnp": mcnp_concrete,
        "density": 2.3,
    },
    "air": {
        "openmc": create_air,
        "mcnp": mcnp_air,
        "density": 0.001225,
    },
    "carbon_steel": {
        "openmc": create_carbon_steel,
        "mcnp": mcnp_carbon_steel,
        "density": 7.82,
    },
    "ss304": {
        "openmc": create_ss304,
        "mcnp": mcnp_ss304,
        "density": 7.94,
    },
    "monel": {
        "openmc": create_monel,
        "mcnp": mcnp_monel,
        "density": 8.80,
    },
}


# =============================================================================
# MATERIAL COLORS (for visualization)
# =============================================================================

MATERIAL_COLORS = {
    # Fissile materials - green tones
    "UF6": (127, 255, 0),           # Chartreuse green
    "UF6_HF": (127, 255, 0),        # Same as UF6
    "HUR_Heel": (50, 205, 50),      # Lime green

    # Structural materials - gray/brown tones
    "Aluminum": (147, 112, 219),    # Medium purple
    "Steel": (105, 105, 105),       # Dim gray
    "Carbon_Steel": (139, 69, 19),  # Saddle brown
    "SS304": (169, 169, 169),       # Dark gray
    "Monel": (184, 115, 51),        # Copper-ish (Ni-Cu alloy)

    # Moderators/reflectors - blue tones
    "Water": (30, 144, 255),        # Dodger blue
    "Concrete": (188, 143, 143),    # Rosy brown

    # Environment
    "Air": (135, 206, 250),         # Light sky blue
}


def get_material_color(name: str) -> tuple[int, int, int]:
    """Get RGB color tuple for a material by name."""
    return MATERIAL_COLORS.get(name, (200, 200, 200))


def get_color_mapping(materials) -> dict:
    """
    Build color mapping dict for OpenMC plots from a Materials object.

    Args:
        materials: OpenMC Materials object or list of Material objects

    Returns:
        Dict mapping Material objects to RGB tuples
    """
    color_mapping = {}
    for mat in materials:
        color_mapping[mat] = get_material_color(mat.name)
    return color_mapping


def get_color_legend(materials) -> dict:
    """
    Build color legend dict for plot annotations.

    Args:
        materials: OpenMC Materials object or list of Material objects

    Returns:
        Dict mapping material names to RGB tuples
    """
    return {mat.name: get_material_color(mat.name) for mat in materials}


def get_material(name: str, solver: str = "openmc", mat_num: int = None):
    """
    Get material by registry name.

    Args:
        name: Material name (e.g., "aluminum", "water")
        solver: "openmc" or "mcnp"
        mat_num: MCNP material number (required for MCNP solver)

    Returns:
        OpenMC Material object or MCNP material card string
    """
    if name not in MATERIAL_REGISTRY:
        raise ValueError(
            f"Unknown material: '{name}'. Available: {list(MATERIAL_REGISTRY.keys())}"
        )

    entry = MATERIAL_REGISTRY[name]

    if solver == "openmc":
        return entry["openmc"]()
    elif solver == "mcnp":
        if mat_num is None:
            raise ValueError("mat_num required for MCNP materials")
        return entry["mcnp"](mat_num)
    else:
        raise ValueError(f"Unknown solver: {solver}")


def get_density(name: str) -> float:
    """Get material density by name."""
    if name not in MATERIAL_REGISTRY:
        raise ValueError(
            f"Unknown material: '{name}'. Available: {list(MATERIAL_REGISTRY.keys())}"
        )
    return MATERIAL_REGISTRY[name]["density"]


# =============================================================================
# CONSULTANT PACKAGE EXPORT
# =============================================================================

def _material_to_yaml(mat: openmc.Material, description: str) -> str:
    """Extract YAML block from OpenMC Material."""
    lines = [
        f"{mat.name.lower()}:",
        f'  description: "{description}"',
        f"  density_g_cm3: {mat.density}",
        "  composition:",
    ]
    for nuc in mat.nuclides:
        lines.append(f"    {nuc.name}: {nuc.percent:.6f}")

    if mat._sab:
        lines.append('  thermal_scattering: "S(α,β) for H in H2O"')

    return "\n".join(lines)


def export_materials_yaml(enrichment_pct: float, uf6_density: float = 5.09) -> str:
    """
    Export all material compositions as YAML for consultant package.

    Args:
        enrichment_pct: U-235 weight percent for UF6
        uf6_density: UF6 density in g/cm3

    Returns:
        YAML-formatted string with all material compositions
    """
    uf6_mat = create_uf6(enrichment_pct, uf6_density)
    uf6_composition = "\n".join(
        f"    {nuc.name}: {nuc.percent:.6f}" for nuc in uf6_mat.nuclides
    )

    yaml_content = f"""# Material Compositions for Independent Verification
#
# These are the exact isotopic compositions used in the calculations.
# Atom fractions are normalized within each material.

uf6:
  description: "Uranium hexafluoride"
  density_g_cm3: {uf6_mat.density}
  enrichment_wt_pct: {enrichment_pct}
  composition:
{uf6_composition}

{_material_to_yaml(create_steel(), "Stainless steel 316 (simplified)")}

{_material_to_yaml(create_aluminum(), "Aluminum 6061")}

{_material_to_yaml(create_water(), "Light water with thermal scattering")}

{_material_to_yaml(create_air(), "Dry air at STP")}

# Nuclear Data Library
nuclear_data:
  library: "ENDF/B-VIII.0"
  temperature: "293 K (room temperature)"
"""
    return yaml_content


def write_materials_yaml(
    output_path: str,
    enrichment_pct: float,
    uf6_density: float = 5.09
) -> None:
    """Write materials YAML file for consultant package."""
    from pathlib import Path
    content = export_materials_yaml(enrichment_pct, uf6_density)
    Path(output_path).write_text(content)
