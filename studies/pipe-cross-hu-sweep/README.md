# Pipe Cross H/U Sweep

This study reruns the reflected `xz` pipe-cross H/U optimization using the
current shared `UO2F2` density formulas. The goal is to identify the peak
moderation ratio for the known pipe-cross geometry and document the basis in a
form a criticality safety engineer can audit.

## Fixed Basis

- Geometry: reflected `xz` pipe-cross cell with `separation_cm = 0.0`
- Pipe dimensions: `pipe_outer_radius_cm = 5.715`, `pipe_wall_thickness_cm = 0.3048`
- Fuel geometry: `gas_core_radius_cm = 4.4102`, `fuel_outer_radius_cm = 5.4102`
- Enrichment: `20.00 wt% U-235`
- `UF6` density: `0.0127 g/cm3`
- Wall material: `aluminum`
- Moderator density: `1.0 g/cm3`
- Boundary conditions: reflective in `x`, `y`, and `z`

## Workflow

See [experiment-plan.md](experiment-plan.md) for the staged execution plan.

- Broad sweep config: `configs/01_broad_sweep.yaml`
- Refined sweep config: `configs/02_refined_sweep.yaml`
- Density traceability helper: `scripts/uo2f2_density_hu_sweep.py`
- Final engineer-facing summary: `report.md`

`uo2f2_density_g_cm3` is intentionally omitted from the study configs. The
model derives `UO2F2` density directly from `h_to_u` and `enrichment_pct`
using the shared ORNL/TM-12292 helper in
`critbuddy/core/materials/uo2f2_physics.py`.
