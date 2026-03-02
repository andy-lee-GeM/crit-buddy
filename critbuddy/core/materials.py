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
    steel.add_nuclide("Fe56", 0.68, percent_type='wo')
    steel.add_nuclide("Cr52", 0.17, percent_type='wo')
    steel.add_nuclide("Ni58", 0.12, percent_type='wo')
    steel.add_nuclide("Mo96", 0.025, percent_type='wo')
    steel.add_nuclide("Mn55", 0.005, percent_type='wo')
    return steel


def create_water(density: float = 1.0) -> openmc.Material:
    """
    Create water with thermal scattering for OpenMC.

    Args:
        density: Water density in g/cm3 (default 1.0, range 0.001 to 1.0)
                 Use lower densities to model mist/fog/steam conditions.
                 Density ~0.001 represents humid air conditions.

    Returns:
        OpenMC Material object for water at specified density.
    """
    # Name reflects density for clarity in outputs
    if density <= 0.01:
        # Very low density water vapor - effectively humid air environment
        name = f"Humid_Air_{density:.3f}"
    elif density < 0.99:
        name = f"Water_{density:.3f}"
    else:
        name = "Water"

    water = openmc.Material(name=name)
    water.set_density("g/cm3", density)
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
    air.add_nuclide("O16", 0.21)
    air.add_nuclide("Ar40", 0.01)
    return air


def create_vacuum() -> openmc.Material:
    """
    Create vacuum material for OpenMC.

    Represents evacuated space (e.g., above liquid in partially filled pipes).
    Uses near-zero density air for visualization in geometry plots.
    """
    vacuum = openmc.Material(name="Vacuum")
    vacuum.set_density("g/cm3", 1e-10)
    vacuum.add_nuclide("N14", 1.0)
    return vacuum


def create_humid_air() -> openmc.Material:
    """
    Create 100% relative humidity air at 40°C for OpenMC.

    Conservative case: higher temperature = more water vapor.

    At 40°C and 1 atm:
    - Saturation vapor pressure: 7.38 kPa (Antoine equation)
    - Water vapor fraction: 7.3% by volume
    - Density: ~0.0011 g/cc

    Composition calculation:
    - Mole fraction H2O: 7.38/101.325 = 0.0728
    - Mole fraction dry air: 0.9272
    - Dry air: N2 (78.08%), O2 (20.95%), Ar (0.93%)

    Atom fractions (normalized):
    - N14: 0.702 (from N2)
    - O16: 0.223 (from O2 + H2O)
    - Ar40: 0.004
    - H1:  0.071 (from H2O)
    """
    humid = openmc.Material(name="Humid_Air")
    humid.set_density("g/cm3", 0.0011)
    humid.add_nuclide("N14", 0.702)
    humid.add_nuclide("O16", 0.223)
    humid.add_nuclide("Ar40", 0.004)
    humid.add_nuclide("H1", 0.071)
    return humid


def create_void() -> openmc.Material:
    """
    Create near-vacuum void material for OpenMC.

    Used for headspace above partial fill in cylinders.
    Modeled as very low density air (essentially no interaction).
    """
    void = openmc.Material(name="Void")
    void.set_density("g/cm3", 0.0001)  # Near-vacuum
    void.add_nuclide("N14", 0.78)
    void.add_nuclide("O16", 0.21)
    void.add_nuclide("Ar40", 0.01)
    return void


def uo2f2_density(h_to_u: float = 0.0) -> float:
    """
    Calculate UO2F2 mixture density from H/U ratio.

    Assumes ideal mixing of crystalline UO2F2 (6.37 g/cc) with water (1.0 g/cc).

    Args:
        h_to_u: Hydrogen atoms per uranium atom (0 = dry, higher = wetter)

    Returns:
        Mixture density in g/cc

    Examples:
        H/U=0:   6.37 g/cc (dry crystal)
        H/U=2:   4.91 g/cc (monohydrate)
        H/U=10:  2.88 g/cc (wet slurry)
        H/U=100: 1.27 g/cc (dilute solution)
    """
    mw_uo2f2 = 308.02  # g/mol (U: 238.03, O: 32, F: 38)
    mw_h2o = 18.015    # g/mol

    v_uo2f2 = mw_uo2f2 / 6.37   # 48.35 cm³/mol
    v_h2o = mw_h2o / 1.0        # 18.015 cm³/mol

    n_water = h_to_u / 2.0  # moles H2O per mole UO2F2

    total_mass = mw_uo2f2 + n_water * mw_h2o
    total_volume = v_uo2f2 + n_water * v_h2o

    return total_mass / total_volume


def create_uo2f2(enrichment_pct: float, h_to_u: float = 0.0,
                 density: float = None) -> openmc.Material:
    """
    Create uranyl fluoride (UO2F2) for OpenMC - dry or wet.

    Reaction: UF6 + 2H2O → UO2F2 + 4HF

    The H/U ratio specifies the degree of hydration:
      H/U = 0:   Dry UO2F2 (crystal, 6.37 g/cc)
      H/U = 2:   Monohydrate UO2F2·H2O
      H/U = 10:  Wet slurry
      H/U = 100: Dilute solution

    Density is auto-calculated from H/U assuming ideal mixing, unless
    explicitly overridden.

    IMPORTANT: UO2F2 contains oxygen which provides internal moderation,
    potentially making it MORE reactive than pure UF6. Adding water (H/U > 0)
    further increases moderation.

    Args:
        enrichment_pct: U-235 weight percent
        h_to_u: H/U atomic ratio (0 = dry, >0 = wet with water)
        density: Override density (if None, calculated from H/U)

    Returns:
        OpenMC Material
    """
    u235_frac, u238_frac = _uranium_fractions(enrichment_pct)

    if density is None:
        density = uo2f2_density(h_to_u)

    # Composition per U atom:
    #   U: 1 (split between U-235 and U-238)
    #   O: 2 (from UO2F2) + h_to_u/2 (from water)
    #   F: 2 (from UO2F2)
    #   H: h_to_u (from water)
    o_atoms = 2.0 + h_to_u / 2.0
    f_atoms = 2.0
    h_atoms = h_to_u

    name = f"UO2F2_H{h_to_u}" if h_to_u > 0 else "UO2F2"
    mat = openmc.Material(name=name)
    mat.set_density("g/cm3", density)
    mat.add_nuclide("U235", u235_frac, percent_type="ao")
    mat.add_nuclide("U238", u238_frac, percent_type="ao")
    mat.add_nuclide("O16", o_atoms, percent_type="ao")
    mat.add_nuclide("F19", f_atoms, percent_type="ao")
    if h_atoms > 0:
        mat.add_nuclide("H1", h_atoms, percent_type="ao")
        mat.add_s_alpha_beta("c_H_in_H2O")  # Thermal scattering for bound hydrogen

    return mat


def create_fissile_material(
    fissile_material: str,
    enrichment_pct: float,
    fissile_density: float = None,
    h_to_u: float = 0.0,
) -> openmc.Material:
    """
    Create fissile material from template-facing material selector.

    Args:
        fissile_material: Material selector ("uf6" or "uo2f2")
        enrichment_pct: U-235 enrichment (wt%)
        fissile_density: Optional density override in g/cm3
        h_to_u: H/U atomic ratio (used for UO2F2)

    Returns:
        OpenMC Material for the selected fissile material
    """
    key = fissile_material.lower()

    if key == "uf6":
        density = 5.09 if fissile_density is None else fissile_density
        return create_uf6(enrichment_pct, density=density)
    if key == "uo2f2":
        # When density is omitted, create_uo2f2() auto-calculates from H/U.
        return create_uo2f2(enrichment_pct, h_to_u=h_to_u, density=fissile_density)

    raise ValueError(f"Unsupported fissile_material '{fissile_material}'")


def create_environment_material(
    environment_material: str,
    environment_density: float = None,
) -> openmc.Material:
    """
    Create environment/reflector material with optional density override.

    Args:
        environment_material: Registry material key (e.g., humid_air, air, water)
        environment_density: Optional density override in g/cm3

    Returns:
        OpenMC Material for the selected environment
    """
    mat = get_material(environment_material, solver="openmc")
    if environment_density is not None:
        mat.set_density("g/cm3", environment_density)
    return mat


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


def mcnp_humid_air(mat_num: int) -> str:
    """Generate MCNP material card for 100% RH air at 40°C (conservative)."""
    return f"""c Material {mat_num}: Humid Air (100% RH, 40C), 0.0011 g/cm3
m{mat_num}   7014.80c   0.702   $ N-14
     8016.80c   0.223   $ O-16 (dry air + H2O)
     18040.80c  0.004   $ Ar-40
     1001.80c   0.071   $ H-1 (from water vapor)
"""


def mcnp_void(mat_num: int) -> str:
    """Generate MCNP material card for near-vacuum void."""
    return f"""c Material {mat_num}: Void (near-vacuum), 0.0001 g/cm3
m{mat_num}   7014.80c   0.78   $ N-14
     8016.80c   0.21   $ O-16
     18040.80c  0.01   $ Ar-40
"""


def mcnp_uo2f2(mat_num: int, enrichment_pct: float, h_to_u: float = 0.0,
               density: float = None) -> str:
    """
    Generate MCNP material card for uranyl fluoride (UO2F2) - dry or wet.

    Args:
        mat_num: MCNP material number
        enrichment_pct: U-235 weight percent
        h_to_u: H/U atomic ratio (0 = dry, >0 = wet with water)
        density: Override density (if None, calculated from H/U)

    Returns:
        MCNP material card string
    """
    u235_frac, u238_frac = _uranium_fractions(enrichment_pct)

    if density is None:
        density = uo2f2_density(h_to_u)

    # Composition per U atom
    o_atoms = 2.0 + h_to_u / 2.0
    f_atoms = 2.0
    h_atoms = h_to_u

    # Total atoms for normalization
    total = u235_frac + u238_frac + o_atoms + f_atoms + h_atoms

    label = f"UO2F2 (H/U={h_to_u})" if h_to_u > 0 else "UO2F2"
    lines = [f"c Material {mat_num}: {label} at {enrichment_pct:.2f} wt% U-235, {density:.4f} g/cm3"]
    lines.append(f"m{mat_num}   92235.80c  {u235_frac/total:.6e}   $ U-235")
    lines.append(f"     92238.80c  {u238_frac/total:.6e}   $ U-238")
    lines.append(f"     8016.80c   {o_atoms/total:.6e}    $ O-16")
    lines.append(f"     9019.80c   {f_atoms/total:.6e}    $ F-19")
    if h_atoms > 0:
        lines.append(f"     1001.80c   {h_atoms/total:.6e}    $ H-1")

    return "\n".join(lines) + "\n"


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
    "humid_air": {
        "openmc": create_humid_air,
        "mcnp": mcnp_humid_air,
        "density": 0.0011,
    },
    "void": {
        "openmc": create_void,
        "mcnp": mcnp_void,
        "density": 0.0001,
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
    # Fissile materials - bright green (high visibility)
    "UF6": (0, 200, 0),             # Bright green
    "UF6_HF": (0, 200, 0),          # Same as UF6
    "UO2F2": (0, 180, 0),           # Slightly darker green (uranyl fluoride)
    "HUR_Heel": (50, 205, 50),      # Lime green

    # Structural materials - dark for visibility
    "Aluminum": (147, 112, 219),    # Medium purple
    "Steel": (50, 50, 50),          # Dark gray (near black for visibility)
    "Carbon_Steel": (60, 60, 60),   # Dark gray
    "SS304": (70, 70, 70),          # Dark gray
    "Monel": (80, 60, 40),          # Dark copper-ish (Ni-Cu alloy)

    # Moderators/reflectors - blue tones
    "Water": (135, 206, 250),       # Light sky blue
    "Concrete": (188, 143, 143),    # Rosy brown

    # Environment
    "Air": (173, 216, 230),         # Light blue
    "Humid_Air": (173, 216, 230),   # Light blue
    "Void": (255, 255, 255),        # White
    "Vacuum": (255, 230, 230),      # Light pink (distinct from humid air)
}


def get_material_color(name: str) -> tuple[int, int, int]:
    """Get RGB color tuple for a material by name."""
    # Handle water at any density (e.g., "Water_0.500")
    if name.startswith("Water"):
        return MATERIAL_COLORS["Water"]
    # Handle UO2F2 with H/U ratio suffix (e.g., "UO2F2_H10", "UO2F2_H30")
    if name.startswith("UO2F2"):
        return MATERIAL_COLORS["UO2F2"]
    # Handle Humid_Air with density suffix (e.g., "Humid_Air_0.001")
    if name.startswith("Humid_Air"):
        return MATERIAL_COLORS["Humid_Air"]
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
