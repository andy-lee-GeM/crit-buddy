# Pipe Cross H/U Sweep

This study stages the first H/U optimization run for the original reflective
`xz` pipe-cross cell. It is set up for review and has not been run yet.

## Fixed Basis

- Geometry: canonical `xz` pipe-cross cell with `gap = 0` (`separation_cm: 0.0`)
- Pipe dimensions: `r_outer = 5.715 cm`, wall thickness `0.3048 cm`
- Fuel annulus: `r_gas = 4.4102 cm`, `r_fuel_outer = 5.4102 cm`
- Enrichment: `20.19 wt% U-235`
- Gas: `UF6` at `0.0127 g/cm3`
- Wall: `aluminum`
- Moderator: water at `1.0 g/cm3`
- Boundaries: reflective in `x`, `y`, and `z`

## Sweep

The study sweeps:

- `h_to_u = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50`

`uo2f2_density_g_cm3` is intentionally omitted. The model derives the UO2F2
density from `h_to_u` and `enrichment_pct` using the shared ORNL/TM-12292
helper in `critbuddy/core/materials/uo2f2_physics.py`.

## Run

```bash
python run_study.py studies/pipe-cross-hu-sweep/study.yaml
```
