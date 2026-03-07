# Example Assumptions: 06 Cylinder Array UF6 Dry Low Fill

This is a fully worked assumptions inventory for one cylinder-array experiment.

## Source files
- Config: `experiments/crit_requests/06_cylinder_array_3d/_config/uf6_dry_low_fill.yaml`
- Template defaults and derivations: `templates/cylinder/__init__.py`
- OpenMC geometry and settings: `templates/cylinder/openmc/model.py`
- Materials: `critbuddy/core/materials.py`
- Global assumptions: `docs/criticality-assumptions.md`
- Cross sections path: `config.yaml`

## Inputs and sweeps
- Problem template: `cylinder`
- Experiment name: "UF6 Dry - Low Fill Sweep"
- Rows: 3
- Cols: 4
- Layers: 5
- Inner radius: 12.70 cm
- Internal height: 100.0 cm
- Wall material: steel
- Wall thickness: 0.3175 cm
- Horizontal gap (wall to wall): 12.70 cm
- Vertical gap (wall to wall): 7.62 cm
- Enrichment: 21 wt% U-235
- Fissile material: UF6
- Fissile density: 5.09 g/cc
- Fill fraction sweep: 0.01, 0.02, 0.05, 0.10, 0.15, 0.20
- Environment: humid_air
- Void material: humid_air
- Boundary type: reflective
- Reflector thickness: 6.35 cm

Defaulted parameters from the template
- H/U: 0.0
- Particles per batch: 10,000
- Total batches: 150
- Inactive batches: 50
- Run mode: eigenvalue

## Derived geometry (units: cm)

Cylinder geometry
- Outer radius: 13.0175
- Total cylinder height (including caps): 100.635
- Wall thickness is used for both wall shell and end caps.

Array spacing
- Spacing XY (center to center): 38.735
- Spacing Z (center to center): 108.255

Array dimensions
- Array X: 103.505
- Array Y: 142.24
- Array Z: 533.655

Bounding box dimensions
- Total X: 116.205
- Total Y: 154.94
- Total Z: 546.355

Array offsets (to center the array at origin)
- X offset: -38.735
- Y offset: -58.1025
- Z offset: -216.51

Outer boundary surfaces
- X planes at x = -58.1025 and +58.1025
- Y planes at y = -77.47 and +77.47
- Z planes at z = -273.1775 and +273.1775
- Boundary condition is reflective on all six planes.

Cylinder center locations
- For row, col, layer indexes starting at 0:
- x_center = -38.735 + row * 38.735
- y_center = -58.1025 + col * 38.735
- z_center = -216.51 + layer * 108.255

Per-cylinder axial planes
- z_bot_cap = z_center - 100.635/2
- z_bot_uf6 = z_bot_cap + 0.3175
- z_top_uf6 = z_bot_uf6 + 100.0
- z_top_cap = z_top_uf6 + 0.3175

Partial fill interpretation
- Fissile height = 100.0 * fill_fraction
- z_uf6_top_actual = z_bot_uf6 + fissile_height
- UF6 occupies z_bot_uf6 to z_uf6_top_actual inside the inner radius.
- Void occupies z_uf6_top_actual to z_top_uf6 inside the inner radius.

Environment region
- Humid air fills the bounding box minus all cylinder volumes, including caps.

Source distribution used in OpenMC
- Box source bounds
- x from -45.085 to +45.085
- y from -64.4525 to +64.4525
- z from -241.51 to +241.51

## Materials and thermal scattering

UF6
- Density: 5.09 g/cc
- Enrichment: 21 wt% U-235
- Atom fractions derived from U-235 and U-238 atomic masses
- U-235 atom fraction: 0.21211673
- U-238 atom fraction: 0.78788327
- UF6 atom fractions for MCNP (normalized to 7 atoms)
- U-235: 0.03030239
- U-238: 0.11255475
- F-19: 0.85714286
- No thermal scattering applied

Steel (stainless steel 316)
- Density: 8.0 g/cc
- Composition from `create_steel` uses weight fractions
- Fe-56: 0.68
- Cr-52: 0.17
- Ni-58: 0.12
- Mo-96: 0.025
- Mn-55: 0.005
- For MCNP, use weight fractions or convert to atom fractions consistently.

Humid air
- Density: 0.0011 g/cc
- N-14: 0.702
- O-16: 0.223
- Ar-40: 0.004
- H-1: 0.071
- No thermal scattering applied

## Physics and solver settings
- Solver: OpenMC
- Run mode: eigenvalue
- Particles per batch: 10,000
- Total batches: 150
- Inactive batches: 50
- Total active histories: 1,000,000
- Nuclear data library: `OPENMC_CROSS_SECTIONS` from `config.yaml`
- Current config path: `/home/andylee/openmc_data/endfb-vii.1-hdf5/cross_sections.xml`
- Temperature: room temperature (293 K)
- No depletion or burnup modeled
- No neutron absorbers or poisons credited

## MCNP reproduction notes
- Use KCODE with 10,000 particles per cycle, 50 inactive cycles, and 150 total cycles.
- Initialize source with KSRC points inside the UF6 regions or an SDEF box matching the OpenMC source bounds.
- Apply reflective boundary conditions to the six outer planes.
- Build each cylinder as inner UF6 region, steel wall shell, and top and bottom steel caps.
- For each fill fraction case, adjust the UF6 top plane to match the fill height and assign humid air above.
- Ensure material cards match the atom or weight fraction basis used in OpenMC.
- If you switch libraries to ENDF/B-VIII.0 for MCNP, expect small differences relative to OpenMC ENDF/B-VII.1 runs.
