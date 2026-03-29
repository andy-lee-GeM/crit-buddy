# UO₂F₂ Density Calculation Basis

## Purpose

This document describes the density calculation methodology for uranyl fluoride (UO₂F₂) solutions and hydrates as a function of uranium enrichment and hydrogen-to-uranium (H/U) atomic ratio. The implementation is based on **ORNL/TM-12292, Appendix A** (Jordan and Turner, 1992).

## Reference Document

- **Title**: Estimated Critical Conditions for UO₂F₂-H₂O Systems in Fully Water-Reflected Spherical Geometry
- **Authors**: W.C. Jordan, J.C. Turner
- **Report**: ORNL/TM-12292, December 1992
- **Location**: [`docs/references/uo2f2-density-ornl-tm-12292.pdf`](../../uo2f2-density-ornl-tm-12292.pdf)
- **Key Section**: Appendix A (pages 13-22 of report, PDF pages 23-32)

## Implementation Location

The density calculations are implemented in:
- **Module**: [`critbuddy/core/materials/uo2f2_physics.py`](../../../critbuddy/core/materials/uo2f2_physics.py)
- **Primary Functions**:
  - `uranium_density()` - General Eq. A.1 implementation
  - `uranyl_fluoride_density()` - UO₂F₂-specific piecewise function
  - `uo2f2_density()` - Bulk mixture density calculator
  - `uo2f2_stoichiometry()` - Complete composition calculator

## Physical Basis

### System Behavior by H/U Ratio

The UO₂F₂-H₂O system exhibits three distinct physical regimes:

| H/U Range | Physical State | Calculation Method |
|-----------|---------------|-------------------|
| **0 ≤ H/U < 4** | Hydrated solid salts (mixtures of UO₂F₂, UO₂F₂·H₂O, UO₂F₂·2H₂O) | Linear fit (Eq. A.2) |
| **4 ≤ H/U < 16** | Slurry (UO₂F₂·2H₂O precipitate + water) | Volume-additive (Eq. A.3) |
| **H/U ≥ 16** | True solution (dissolved uranyl fluoride) | Volume-additive (Eq. A.3) |

### Critical Transition Points

1. **H/U = 4**: Transition from hydrated solids to slurries (discontinuity in density function)
2. **H/U ≈ 16**: Saturation limit - above this, UO₂F₂ is fully dissolved

## Mathematical Formulation

### General Equation (ORNL Eq. A.1)

For a uranium compound with moderator, the uranium density is:

```
ρᵤ = Mᵤ / [(Vᵤc/N) + (H/U - M×Y) × (Vₘ/M)]
```

Where:
- **ρᵤ** = uranium density (g/cm³)
- **Mᵤ** = molecular weight of uranium at given enrichment (g/mol)
- **Vᵤc** = molar volume of uranium compound (cm³/mol)
- **N** = number of uranium atoms per formula unit
- **Vₘ** = molar volume of moderator compound (cm³/mol)
- **M** = number of hydrogen atoms per moderator molecule
- **Y** = number of hydrated moderator molecules in uranium compound
- **H/U** = hydrogen-to-uranium atomic ratio

### UO₂F₂-Specific Implementation

#### Region 1: Hydrated Solids (H/U < 4)

**ORNL Eq. A.2**:
```
ρᵤ = 4.96 - 0.32 × (H/U)
```

This is a **linear fit** with:
- Intercept at H/U = 0: ρᵤ = 4.96 g/cm³ (anhydrous UO₂F₂)
- Endpoint at H/U = 4: ρᵤ = 3.68 g/cm³

**Physical basis**: Below H/U = 4, only solid hydrate phases exist. The linear fit bounds the densities of UO₂F₂, UO₂F₂·H₂O, and UO₂F₂·2H₂O.

#### Region 2: Solutions/Slurries (H/U ≥ 4)

**ORNL Eq. A.3**:
```
ρᵤ = Mᵤ / [V(UO₂F₂·2H₂O) + (H/U - 4) × (V(H₂O)/2)]
```

This is the **volume-additive formulation** assuming:
- Base compound: UO₂F₂·2H₂O (uranyl fluoride dihydrate)
- Excess water: (H/U - 4) moles of H per U beyond the dihydrate

**Physical basis**: Above H/U = 4, the system is modeled as UO₂F₂·2H₂O mixed with excess water. The dihydrate has 4 H atoms per U (2 waters × 2 H per water), so (H/U - 4) accounts for additional free water.

## Implementation Constants

### Isotopic Masses (`IsotopicMasses` dataclass)

| Constant | Value (g/mol) | Source |
|----------|---------------|--------|
| `u235_g_per_mol` | 235.044 | ORNL/TM-12292 Table A.1 |
| `u238_g_per_mol` | 238.051 | ORNL/TM-12292 Table A.1 |
| `o16_g_per_mol` | 15.999 | ORNL/TM-12292 Table A.1 |
| `f19_g_per_mol` | 18.998403163 | ORNL/TM-12292 Table A.1 |
| `h2o_g_per_mol` | 18.015 | ORNL/TM-12292 Table A.1 (calculated: 2×1.008 + 15.999) |

### UO₂F₂ Model Parameters (`UranylFluorideModel` dataclass)

**Note**: Constants are named to match ORNL/TM-12292 notation from Eq. A.1.

| Constant | Value | Units | ORNL Symbol | Description |
|----------|-------|-------|-------------|-------------|
| `N` | 1.0 | atoms | N | Uranium atoms per formula unit |
| `M` | 2.0 | atoms | M | Hydrogen atoms per water molecule |
| `Y` | 2.0 | molecules | Y | Waters of hydration (UO₂F₂·2H₂O) |
| `Vuc` | 72.2809 | cm³/mol | Vᵤc | Molar volume of UO₂F₂·2H₂O |
| `Vm` | 18.0574 | cm³/mol | Vₘ | Molar volume of H₂O |
| `h_over_u_transition` | 4.0 | - | - | H/U transition point between Eq. A.2 and A.3 |
| `rho_u_intercept` | 4.96 | g/cm³ | - | Uranium density at H/U=0 (Eq. A.2) |
| `slope` | 0.32 | g/cm³ | - | Linear fit slope for H/U < 4 (Eq. A.2) |

### Derivation of Molar Volumes

From **ORNL Table A.1** (page 25, PDF page 35):

#### UO₂F₂·2H₂O (Uranyl Fluoride Dihydrate)
- Molecular weight: 344.057 g/mol
- Theoretical density @ 23°C: 4.76 g/cm³
- **Specific molar volume** (Vᵤc/N): 72.2809 cm³/mol
- Calculation: `Vᵤc = (344.057 g/mol) / (4.76 g/cm³) = 72.2809 cm³/mol`

#### H₂O (Water)
- Molecular weight: 18.016 g/mol
- Density @ 23°C: 0.9977 g/cm³
- **Specific molar volume per H atom** (Vₘ/M): 9.0287 cm³/mol
- **Molar volume**: Vₘ = 9.0287 × 2 = 18.0574 cm³/mol
- Calculation: `Vm = (18.016 g/mol) / (0.9977 g/cm³) = 18.0574 cm³/mol`

## Calculation Procedure

### Step 1: Calculate Uranium Molar Mass

For a given enrichment (wt% ²³⁵U):

```python
def uranium_molar_mass(enrichment_pct: float) -> float:
    w235 = enrichment_pct / 100.0
    w238 = 1.0 - w235

    # Convert weight fractions to mole fractions
    n235 = w235 / 235.044
    n238 = w238 / 238.051
    total = n235 + n238

    x235 = n235 / total
    x238 = n238 / total

    # Average atomic mass
    Mu = x235 * 235.044 + x238 * 238.051
    return Mu
```

### Step 2: Calculate Uranium Density

```python
def uranyl_fluoride_density(H_over_U: float, Mu: float) -> float:
    if H_over_U < 4.0:
        # Region 1: Hydrated solids (Eq. A.2)
        rho_u = 4.96 - 0.32 * H_over_U
    else:
        # Region 2: Solutions/slurries (Eq. A.3)
        Vuc = 72.2809  # UO2F2·2H2O molar volume
        Vm = 18.0574   # H2O molar volume
        N = 1.0        # U atoms per formula
        M = 2.0        # H atoms per water
        Y = 2.0        # Waters of hydration

        specific_uc = Vuc / N  # = 72.2809
        specific_m = Vm / M    # = 9.0287
        denominator = specific_uc + (H_over_U - M * Y) * specific_m
        rho_u = Mu / denominator

    return rho_u
```

### Step 3: Calculate Bulk Mixture Density

The bulk density includes both UO₂F₂ and water:

```python
def uo2f2_bulk_density(h_to_u: float, enrichment_pct: float) -> float:
    # Step 1: Get uranium molar mass
    Mu = uranium_molar_mass(enrichment_pct)

    # Step 2: Get uranium density
    rho_u = uranyl_fluoride_density(h_to_u, Mu)

    # Step 3: Calculate total mass per mole of uranium
    # UO2F2 mass per U
    m_uo2f2 = Mu + 2*15.999 + 2*18.998403163

    # Water mass per U
    n_water = h_to_u / 2.0  # moles of H2O per U
    m_water = n_water * 18.015

    # Total mass
    total_mass = m_uo2f2 + m_water

    # Bulk density
    rho_bulk = rho_u * total_mass / Mu
    return rho_bulk
```

## Validation Examples

### Example 1: Anhydrous UO₂F₂ (H/U = 0)

For 20% enriched uranium:
- Mᵤ = 237.443 g/mol
- ρᵤ = 4.96 g/cm³ (from Eq. A.2)
- Bulk ρ = 4.96 × (307.44) / 237.443 = **6.42 g/cm³**

### Example 1a: Hydrated Salt Distinction (H/U = 3)

For 20% enriched uranium:
- Mᵤ = 237.443 g/mol
- ρᵤ = 4.96 - 0.32 × 3 = **4.00 g/cm³**
- This `ρᵤ` value is the **uranium density**, not the total mixture density
- Bulk ρ = 4.00 × (334.46) / 237.443 = **5.63 g/cm³**
- Dry UO₂F₂ component density = **5.18 g/cm³**
- H₂O component density = **0.46 g/cm³**

### Example 2: UO₂F₂·2H₂O (H/U = 4)

For 20% enriched uranium at H/U = 4:
- From Eq. A.2: ρᵤ = 4.96 - 0.32 × 4 = **3.68 g/cm³**
- From Eq. A.3: ρᵤ = 237.443 / [72.2809 + (4-4) × 9.0287] = **3.29 g/cm³**

**Note**: The discontinuity at H/U = 4 is expected and conservative (Eq. A.2 predicts higher density).

### Example 3: Dilute Solution (H/U = 500)

For 100% enriched uranium at H/U = 500:
- Mᵤ = 235.044 g/mol
- ρᵤ = 235.044 / [72.2809 + (500-4) × 9.0287] = **0.0517 g/cm³**
- ORNL Table A.3 reports: **0.05169 g/cm³** ✓

## Conservative Features

The formulation is designed to be **conservative** (slightly overpredict densities):

1. **Discontinuity at H/U = 4**: The linear fit (Eq. A.2) gives higher densities than the volume-additive model (Eq. A.3) at the transition point
2. **Theoretical densities used**: Actual solution densities may be slightly lower than theoretical calculations
3. **No temperature corrections**: Default values are at 23°C; lower temperatures would increase density

## Temperature Corrections (Future Enhancement)

ORNL Table A.2 provides temperature-dependent density corrections. The current implementation uses **fixed 23°C values**. For temperature-dependent calculations:

```python
def water_density_at_temp(temp_celsius: float) -> float:
    """ORNL Table A.2"""
    t = temp_celsius
    return 0.99987 / (1.0 - 6.427e-5*t + 8.5053e-6*t**2 - 6.79e-8*t**3)
```

## Usage in Crit-Buddy

The density calculations are used by:

1. **Material Builder** ([`builders.py`](../../../critbuddy/core/materials/builders.py)):
   ```python
   def uo2f2(enrichment_pct: float, h_to_u: float, density: float) -> openmc.Material:
       """Create UO2F2 with explicit H/U ratio"""
       stoich = uo2f2_stoichiometry(h_to_u=h_to_u, enrichment_pct=enrichment_pct)
       # ...builds OpenMC material with correct atom ratios
   ```

2. **Configuration System**: Models specify `h_to_u` in their configs, and the density is automatically calculated

3. **Independent Review**: Density values are included in reproducibility reports

## Testing

Unit tests verify the implementation against ORNL Table A.3:
- **Test File**: [`tests/unit/materials/test_uo2f2_physics.py`](../../../tests/unit/materials/test_uo2f2_physics.py)
- **Coverage**: Multiple enrichments (1.4% to 100%) and H/U ratios (0 to 2000)
- **Tolerance**: Densities must match ORNL values within 0.1%

## References

1. **Primary Source**:
   - Jordan, W.C. and Turner, J.C., "Estimated Critical Conditions for UO₂F₂-H₂O Systems in Fully Water-Reflected Spherical Geometry," ORNL/TM-12292, Oak Ridge National Laboratory, December 1992.
   - Appendix A: Density Relationships (pages 13-22)

2. **Related Standards**:
   - ANSI/ANS-8.1: Nuclear Criticality Safety in Operations with Fissionable Materials Outside Reactors
   - ANSI/ANS-8.15: Nuclear Criticality Control of Special Actinide Elements

3. **OpenMC Material Documentation**:
   - OpenMC User's Guide: https://docs.openmc.org/

## Change History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-03-18 | 1.0 | Initial basis document | - |

---

**Document Classification**: Technical Basis
**Review Status**: Initial Draft
**Next Review**: Before any modification to `uo2f2_physics.py` density calculations
