# MCNP Reference Case Analysis

## Model Overview
**Title:** Piping Model - Infinite Lattice  
**Configuration:** Two-pipe array with reflective boundaries (infinite lattice approximation)

## Geometry Parameters

### Pipe 1 (centered at origin)
- **Outer radius:** 5.715 cm (surface 1)
- **Wall inner radius:** 5.4102 cm (surface 2)
- **Wall thickness:** 0.3048 cm
- **Solution radius:** 4.4102 cm (surface 11)
- **Gas gap thickness:** 1.0 cm (between solution and wall)

### Pipe 2 (offset pipe)
- **Center location:** x = 11.43 cm, y = 0
- **Pipe pitch (center-to-center):** 11.43 cm
- **Same radii as Pipe 1**

### Boundary Conditions
- **Height (Z):** -8.715 to 8.715 cm (17.43 cm total)
- **X boundaries:** -8.715 to 8.815 cm
- **Y boundaries:** -8.715 to 20.145 cm
- **Reflective surfaces (*):** All boundary planes are reflective → infinite lattice

## Materials

### Material 1: UF6 Gas (headspace)
- **Density:** 0.0127 g/cm³
- **Composition:**
  - U-235: 5.06×10⁻⁵ atom/b-cm
  - U-238: 3.32×10⁻⁵ atom/b-cm
  - F-19: 1.5×10⁻⁴ atom/b-cm
- **Enrichment:** ~60.4% (based on U-235/(U-235+U-238))

### Material 2: Aluminum (pipe walls)
- **Density:** 2.70 g/cm³
- **Composition:** Al-27: 0.06022 atom/b-cm

### Material 3: Water (reflector/moderator)
- **Density:** 1.0 g/cm³
- **Composition:**
  - H-1: 0.067 atom/b-cm
  - O-16: 0.033 atom/b-cm
- **Thermal scattering:** lwtr.01t

### Material 4: Air (not used in cells)
- N-14, O-16, Ar-40, H-1

### Material 5: UO2F2 Solution (fissile material)
- **Density:** 6.37 g/cm³
- **Composition:**
  - U-235: 0.00252 atom/b-cm
  - U-238: 0.00996 atom/b-cm
  - O-16: 0.02496 atom/b-cm
  - F-19: 0.02496 atom/b-cm
- **Enrichment:** 20.19% (matches AD-7 requirement of 20.2%)

## Fill Configuration
- **Fill height:** Not explicitly defined by material cards
- **Likely full fill** based on cell definitions (cells 4 and 6 span full height)

## Cell Assignments
1. **Cell 1:** Pipe 1 wall (aluminum)
2. **Cell 3:** Water reflector around pipes
3. **Cell 4:** UO2F2 solution in Pipe 1
4. **Cell 5:** UF6 gas in Pipe 1 (headspace or void)
5. **Cell 6:** UO2F2 solution in Pipe 2
6. **Cell 7:** UF6 gas in Pipe 2
7. **Cell 8:** Pipe 2 wall (aluminum)

## Criticality Settings
- **Mode:** Neutron transport
- **KCODE:** 4800 neutrons/cycle, k-eff guess 1.0, 50 skip cycles, 200 active cycles
- **Source:** Single point at origin (0, 0, 0)

## Key Observations for OpenMC Model

1. **This is a 2-pipe infinite lattice** - reflective boundaries simulate infinite array
2. **Pipe spacing:** 11.43 cm center-to-center
3. **Edge-to-edge spacing:** 11.43 - 2×5.715 = 0 cm (pipes nearly touching!)
4. **Water moderator** surrounds the pipes
5. **Full-height fill** appears to be the configuration (no partial fill)

## Parameters to Match in OpenMC
- Enrichment: 20.2% U-235
- Pipe OD: 5.715 cm
- Pipe wall thickness: 0.3048 cm
- Solution radius: 4.4102 cm
- UO2F2 density: 6.37 g/cm³
- Aluminum wall density: 2.70 g/cm³
- Pipe pitch: 11.43 cm
- Reflective boundaries for infinite lattice
