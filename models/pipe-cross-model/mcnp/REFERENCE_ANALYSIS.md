# MCNP Reference Case Analysis

## Model Overview
**Title:** Piping Model - Infinite Lattice
**Configuration:** Reflected `x-z` pipe crossing (infinite lattice approximation)

## Geometry Parameters

### Z-directed Pipe (centered at origin)
- **Outer radius:** 5.715 cm (surface 1)
- **Wall inner radius:** 5.4102 cm (surface 2)
- **Wall thickness:** 0.3048 cm
- **Solution radius:** 4.4102 cm (surface 11)
- **Gas gap thickness:** 1.0 cm (between solution and wall)

### X-directed Pipe
- **Axis offset:** y = 11.43 cm, z = 0 (surfaces 12-14)
- **Center-to-center spacing:** 11.43 cm
- **Same radii as the z-directed pipe**

## Boundary Conditions
- **Height / x-extent:** -8.715 to 8.815 cm
- **Y boundaries:** -8.715 to 20.145 cm
- **Z boundaries:** -8.715 to 8.715 cm
- **Reflective surfaces (`*`):** all outer planes are reflective

## Materials

### Material 1: UF6 Gas
- **Density:** 0.0127 g/cm³
- **Composition:**
  - U-235: 5.06×10⁻⁵ atom/b-cm
  - U-238: 3.32×10⁻⁵ atom/b-cm
  - F-19: 1.5×10⁻⁴ atom/b-cm
- **Effective enrichment:** ~60.4%

### Material 2: Aluminum
- **Density:** 2.70 g/cm³
- **Composition:** Al-27: 0.06022 atom/b-cm

### Material 3: Water
- **Density:** 1.0 g/cm³
- **Composition:**
  - H-1: 0.067 atom/b-cm
  - O-16: 0.033 atom/b-cm
- **Thermal scattering:** lwtr.01t

### Material 4: Air
- Defined but not used in any cell.

### Material 5: UO2F2 Solution
- **Density:** 6.37 g/cm³
- **Composition:**
  - U-235: 0.00252 atom/b-cm
  - U-238: 0.00996 atom/b-cm
  - O-16: 0.02496 atom/b-cm
  - F-19: 0.02496 atom/b-cm
- **Enrichment:** 20.19%

## Cell Assignments
1. **Cell 1:** z-directed pipe wall (aluminum)
2. **Cell 3:** water reflector around both pipes
3. **Cell 4:** UO2F2 annulus in the z-directed pipe
4. **Cell 5:** UF6 gas core in the z-directed pipe
5. **Cell 6:** UO2F2 annulus in the x-directed pipe
6. **Cell 7:** UF6 gas core in the x-directed pipe
7. **Cell 8:** x-directed pipe wall (aluminum)

## Criticality Settings
- **Mode:** neutron transport
- **KCODE:** 4800 neutrons/cycle, initial guess 1.0, 50 inactive, 200 active
- **Source:** point source at (0, 0, 0)

## Key Observations for OpenMC

1. This is an `x-z` crossing model, not a linear parallel-pipe model.
2. The crossing uses a zero outer-wall gap: `11.43 - 2 * 5.715 = 0 cm`.
3. The outer box is asymmetric in `x` and `y`, matching the literal MCNP deck.
4. All outer planes are reflective, so the deck represents a repeated lattice cell.
5. The gas and fuel isotopics are defined separately and should be treated as separate parity targets.
