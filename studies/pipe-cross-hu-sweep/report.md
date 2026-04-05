# Pipe Cross H/U Sweep Report

This report documents the April 5, 2026 rerun of the reflected `xz` pipe-cross
`H/U` optimization using the current shared `UO2F2` density formulas. The study
was executed in two stages:

- Broad sweep: `runs/01_broad_sweep/latest/results.csv`
- Refined sweep: `runs/02_refined_sweep/latest/results.csv`

The merged results and density traceability tables are packaged under
`results/`.

## Objective

Identify the most reactive `H/U` for the known reflected pipe-cross geometry
and document how each `H/U` value maps to the `UO2F2` densities used by OpenMC.

## Fixed Basis

- Model: `pipe-cross-model`
- Geometry: reflected `xz` crossing
- Separation: `0.0 cm`
- Pipe outer radius: `5.715 cm`
- Pipe wall thickness: `0.3048 cm`
- Gas core radius: `4.4102 cm`
- Fuel outer radius: `5.4102 cm`
- Enrichment: `20.00 wt% U-235`
- `UF6` density: `0.0127 g/cm3`
- Wall material: `aluminum`
- Moderator density: `1.0 g/cm3`
- Boundary conditions: reflective in `x`, `y`, and `z`

## Density Traceability

The study intentionally omits `uo2f2_density_g_cm3` from the configs. The model
derives `UO2F2` density directly from `h_to_u` and `enrichment_pct` using the
shared ORNL/TM-12292 implementation in:

- `critbuddy/core/materials/uo2f2_physics.py`
- `docs/references/materials/uo2f2-density-basis.md`
- `tests/unit/materials/test_uo2f2_physics.py`

Per-point density exports were generated with
`scripts/uo2f2_density_hu_sweep.py` and saved to:

- `results/01_broad_sweep_density_traceability.csv`
- `results/02_refined_sweep_density_traceability.csv`
- `results/combined_hu_results.csv`

Recommended point density basis at `H/U = 3.5`:

| Quantity | Value |
| --- | ---: |
| `bulk_density_g_cm3` | `5.48182604` |
| `uranium_density_g_cm3` | `3.84000000` |
| `uo2f2_component_density_g_cm3` | `4.97197498` |
| `h2o_component_density_g_cm3` | `0.50985106` |
| `water_weight_fraction` | `0.09300752` |
| `water_moles_per_u` | `1.75000000` |
| `density_basis_region` | `hydrated_salt_linear_fit` |

## Results Summary

- The broad sweep reproduced the historical coarse-grid response and again
  ranked `H/U = 3.0` as the highest sampled broad-grid point.
- The refined sweep found a slightly higher maximum at `H/U = 3.5`.
- The refined peak remains broad. `H/U = 2.5`, `3.0`, and `3.5` are all within
  about `0.0012 delta k-eff` in `k+2sigma`.
- The broad sweep transition from `MARGINAL` to `SAFE` remains between
  `H/U = 20` and `H/U = 30`.

## Recommended Engineering Point

For this reflected pipe-cross basis, the preferred sampled moderation point is:

| Recommended `H/U` | `k-eff` | `std` | `k+2sigma` | Status |
| ---: | ---: | ---: | ---: | --- |
| `3.5` | `1.11426` | `0.00121` | `1.11669` | `CRITICAL` |

This recommendation is specific to the idealized reflected `gap = 0` unit-cell
model. It identifies the most reactive sampled moderation state for this study;
it is not a plant operating limit by itself.

## Broad Sweep Results

| H/U | Bulk density (g/cm3) | `k-eff` | `std` | `k+2sigma` | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.0 | 6.42213435 | 1.10771 | 0.00114 | 1.10999 | CRITICAL |
| 1.0 | 6.18382311 | 1.11114 | 0.00120 | 1.11353 | CRITICAL |
| 2.0 | 5.92123325 | 1.11103 | 0.00114 | 1.11331 | CRITICAL |
| 3.0 | 5.63436476 | 1.11318 | 0.00122 | 1.11561 | CRITICAL |
| 4.0 | 4.75185377 | 1.10160 | 0.00118 | 1.10396 | CRITICAL |
| 5.0 | 4.33498341 | 1.09488 | 0.00118 | 1.09725 | CRITICAL |
| 6.0 | 4.00143978 | 1.08802 | 0.00134 | 1.09069 | CRITICAL |
| 7.0 | 3.72850913 | 1.08069 | 0.00126 | 1.08321 | CRITICAL |
| 8.0 | 3.50104540 | 1.07392 | 0.00121 | 1.07634 | CRITICAL |
| 9.0 | 3.30856080 | 1.06926 | 0.00124 | 1.07173 | CRITICAL |
| 10.0 | 3.14356285 | 1.05944 | 0.00114 | 1.06172 | CRITICAL |
| 20.0 | 2.24964476 | 0.99010 | 0.00104 | 0.99218 | MARGINAL |
| 30.0 | 1.88147334 | 0.92652 | 0.00128 | 0.92907 | SAFE |
| 40.0 | 1.68063068 | 0.87366 | 0.00115 | 0.87596 | SAFE |
| 50.0 | 1.55416644 | 0.82409 | 0.00108 | 0.82626 | SAFE |

## Refined Sweep Results

| H/U | Bulk density (g/cm3) | `k-eff` | `std` | `k+2sigma` | Status |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0.5 | 6.30601356 | 1.10908 | 0.00127 | 1.11162 | CRITICAL |
| 1.0 | 6.18382311 | 1.11114 | 0.00120 | 1.11353 | CRITICAL |
| 1.5 | 6.05556301 | 1.11061 | 0.00120 | 1.11302 | CRITICAL |
| 2.0 | 5.92123325 | 1.11103 | 0.00114 | 1.11331 | CRITICAL |
| 2.5 | 5.78083383 | 1.11300 | 0.00126 | 1.11552 | CRITICAL |
| 3.0 | 5.63436476 | 1.11318 | 0.00122 | 1.11561 | CRITICAL |
| 3.5 | 5.48182604 | 1.11426 | 0.00121 | 1.11669 | CRITICAL |
| 4.0 | 4.75185377 | 1.10160 | 0.00118 | 1.10396 | CRITICAL |
| 4.5 | 4.53116588 | 1.09867 | 0.00116 | 1.10098 | CRITICAL |
| 5.0 | 4.33498341 | 1.09488 | 0.00118 | 1.09725 | CRITICAL |

## Artifacts

- Broad results: `runs/01_broad_sweep/latest/results.csv`
- Refined results: `runs/02_refined_sweep/latest/results.csv`
- Geometry validation: `_validation/geometry.png`
- Broad plot: `results/plots/01_broad_sweep_keff_vs_h_to_u.png`
- Refined plot: `results/plots/02_refined_sweep_keff_vs_h_to_u.png`
- Combined results: `results/combined_hu_results.csv`

## Interpretation

The rerun confirms that the reflected pipe-cross model remains most reactive in
the low-hydration regime. On the updated study package, the coarse broad sweep
still points to `H/U = 3.0`, while the refined `0.5`-step sweep shifts the
highest sampled point to `H/U = 3.5`. The peak is still flat enough that this
should be treated as a narrow optimum band centered on `H/U = 3-3.5`, not a
knife-edge single-point result.
