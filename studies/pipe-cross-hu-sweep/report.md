# Pipe Cross H/U Sweep Report

This report summarizes the completed OpenMC H/U sweep for the reflected `xz`
pipe-cross model at `20.00 wt%` enrichment. The detailed generated run report
for this execution is [REPORT.md](/mnt/c/Users/AndyLee/Projects/crit-buddy/studies/pipe-cross-hu-sweep/runs/study/2026-03-24_15-24-53/REPORT.md), and the raw data are in [results.csv](/mnt/c/Users/AndyLee/Projects/crit-buddy/studies/pipe-cross-hu-sweep/runs/study/2026-03-24_15-24-53/results.csv).

## Basis

- Model: `pipe-cross-model`
- Geometry: reflective `xz` crossing
- Separation: `0.0 cm`
- Enrichment: `20.00 wt% U-235`
- UF6 density: `0.0127 g/cm3`
- Wall material: `aluminum`
- Moderator: water at `1.0 g/cm3`
- Sweep: `H/U = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50`

The UO2F2 density values below come from the repo's density sweep script,
which uses the shared ORNL-based physics in
`critbuddy/core/materials/uo2f2_physics.py`.

## Density Check

The `H/U = 3` density was checked directly with:

```bash
python scripts/uo2f2_density_hu_sweep.py --enrichments 20 --h-start 3 --h-stop 3 --h-step 1 --format csv
```

Script output:

```csv
enrichment_wt_pct,h_to_u,bulk_density_g_cm3,uo2f2_component_density_g_cm3,h2o_component_density_g_cm3,water_weight_fraction,region
20,3,5.63436476,5.17914060,0.45522416,0.08079423,hydrated_salt
```

So for this run basis:

- Bulk UO2F2 density at `H/U = 3` is `5.63436476 g/cm3`
- Dry UO2F2 component density is `5.17914060 g/cm3`
- Bound water component density is `0.45522416 g/cm3`
- Water weight fraction is `0.08079423`

## Summary

- The highest sampled reactivity occurred at `H/U = 3` with `k-eff = 1.11318 +/- 0.00122`.
- The low-H/U maximum is broad. `H/U = 1-3` all returned essentially the same peak region within Monte Carlo uncertainty.
- All cases from `H/U = 0` through `H/U = 10` were `CRITICAL`.
- `H/U = 20` was `MARGINAL` with `k-eff = 0.99010`.
- `H/U = 30, 40, 50` were `SAFE`.

## Results Table

| H/U | UO2F2 density (g/cm3) | k-eff | std | k+2sigma | status |
| ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 6.422134 | 1.10771 | 0.00114 | 1.10999 | CRITICAL |
| 1 | 6.183823 | 1.11114 | 0.00120 | 1.11353 | CRITICAL |
| 2 | 5.921233 | 1.11103 | 0.00114 | 1.11331 | CRITICAL |
| 3 | 5.634365 | 1.11318 | 0.00122 | 1.11561 | CRITICAL |
| 4 | 4.751854 | 1.10160 | 0.00118 | 1.10396 | CRITICAL |
| 5 | 4.334983 | 1.09488 | 0.00118 | 1.09725 | CRITICAL |
| 6 | 4.001440 | 1.08802 | 0.00134 | 1.09069 | CRITICAL |
| 7 | 3.728509 | 1.08069 | 0.00126 | 1.08321 | CRITICAL |
| 8 | 3.501045 | 1.07392 | 0.00121 | 1.07634 | CRITICAL |
| 9 | 3.308561 | 1.06926 | 0.00124 | 1.07173 | CRITICAL |
| 10 | 3.143563 | 1.05944 | 0.00114 | 1.06172 | CRITICAL |
| 20 | 2.249645 | 0.99010 | 0.00104 | 0.99218 | MARGINAL |
| 30 | 1.881473 | 0.92652 | 0.00128 | 0.92907 | SAFE |
| 40 | 1.680631 | 0.87366 | 0.00115 | 0.87596 | SAFE |
| 50 | 1.554166 | 0.82409 | 0.00108 | 0.82626 | SAFE |

## Interpretation

For this reflected `gap = 0` configuration, the most reactive region is the
low-hydration regime, with a practical optimum around `H/U = 1-3` and the
highest sampled point at `H/U = 3`. Reactivity then falls steadily with
increasing hydration. The transition from clearly supercritical to subcritical
occurs between `H/U = 20` and `H/U = 30` on this grid.
