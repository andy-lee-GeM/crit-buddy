# Experiment: Pipe-Cross H/U Sweep

## Objective

Rerun the reflected pipe-cross `H/U` optimization using the current shared
`UO2F2` density formulas, identify the most reactive `H/U` for the known
geometry basis, and produce a simple report that documents both the criticality
results and the density traceability.

---

## Request Summary

| Field | Value |
|-------|-------|
| Study ID | `pipe-cross-hu-sweep` |
| Workspace | `studies/pipe-cross-hu-sweep/` |
| Model | `pipe-cross-model` |
| Geometry basis | Reflected `xz` crossing, `separation_cm = 0.0` |
| Enrichment | `20.00 wt%` |
| Setup Date | `2026-04-05` |
| Stage | Ready for execution |

---

## Fixed Geometry Basis

| Parameter | Value |
|-----------|-------|
| `cross_mode` | `xz` |
| `pipe_size` | `custom` |
| `pipe_outer_radius_cm` | `5.715` |
| `pipe_wall_thickness_cm` | `0.3048` |
| `gas_core_radius_cm` | `4.4102` |
| `fuel_outer_radius_cm` | `5.4102` |
| `separation_cm` | `0.0` |
| `uf6_density_g_cm3` | `0.0127` |
| `wall_material` | `aluminum` |
| `moderator_density_g_cm3` | `1.0` |
| `x_boundary_type` | `reflective` |
| `y_boundary_type` | `reflective` |
| `z_boundary_type` | `reflective` |

---

## Density Traceability Basis

`UO2F2` density is derived from `h_to_u` and `enrichment_pct` using:

- `critbuddy/core/materials/uo2f2_physics.py`
- `docs/references/materials/uo2f2-density-basis.md`
- `tests/unit/materials/test_uo2f2_physics.py`

To make that derivation traceable in the study outputs, this workflow exports
per-point density tables with:

- `h_to_u`
- `uranium_density_g_cm3`
- `bulk_density_g_cm3`
- `uo2f2_component_density_g_cm3`
- `h2o_component_density_g_cm3`
- `water_weight_fraction`
- `water_moles_per_u`
- `density_basis_region`

---

## Standard Configs

| # | Config | Purpose | Status |
|---|--------|---------|--------|
| 1 | `configs/01_broad_sweep.yaml` | Confirm the overall `H/U` response on the current density basis | READY |
| 2 | `configs/02_refined_sweep.yaml` | Refine the low-`H/U` peak region identified in prior work | READY |

---

## Run Sequence

### Step 1: Broad Sweep

Purpose: rerun the historical engineering grid and confirm the current peak
region after the density-formula update.

```bash
python run_study.py studies/pipe-cross-hu-sweep/configs/01_broad_sweep.yaml
python scripts/uo2f2_density_hu_sweep.py --enrichment 20.0 --h-values 0,1,2,3,4,5,6,7,8,9,10,20,30,40,50 --format csv
```

After completion:

- Read `runs/01_broad_sweep/latest/results.csv`
- Confirm the broad peak region using the highest `keff + 2sigma`
- Export the matching density traceability table for the sampled `H/U` values

### Step 2: Refined Sweep

Purpose: tighten the peak region around the known low-`H/U` maximum.

```bash
python run_study.py studies/pipe-cross-hu-sweep/configs/02_refined_sweep.yaml
python scripts/uo2f2_density_hu_sweep.py --enrichment 20.0 --h-values 0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0,4.5,5.0 --format csv
```

After completion:

- Read `runs/02_refined_sweep/latest/results.csv`
- Identify the preferred `H/U` using the highest `keff + 2sigma`
- Compare the refined peak against the broad-sweep result
- Export the matching density traceability table for the refined points

---

## Success Criteria

- The reflected `xz` pipe-cross basis is rerun on the current density formulas
- The broad peak region is confirmed
- A refined sweep identifies the preferred engineering `H/U`
- Study artifacts explicitly show how `H/U` mapped to `UO2F2` density
- `report.md` summarizes the basis, results, and recommendation in plain engineering language

### Safety Classification

| Status | Criterion |
|--------|-----------|
| SAFE | `keff + 2sigma < 0.95` |
| MARGINAL | `0.95 <= keff + 2sigma < 1.00` |
| CRITICAL | `keff + 2sigma >= 1.00` |

---

## Expected Artifacts

### Run Outputs

- `runs/01_broad_sweep/latest/results.csv`
- `runs/02_refined_sweep/latest/results.csv`

### Density Traceability

- `results/01_broad_sweep_density_traceability.csv`
- `results/02_refined_sweep_density_traceability.csv`
- `results/combined_hu_results.csv`

### Final Report Package

- `report.md`
- `results/plots/01_broad_sweep_keff_vs_h_to_u.png`
- `results/plots/02_refined_sweep_keff_vs_h_to_u.png`

---

## Notes

1. The refined sweep intentionally focuses on `H/U = 0.5` to `5.0` because prior work placed the peak in the `1-3` region.
2. The shared ORNL-based model uses a low-`H/U` linear fit below `H/U = 4.0`; this remains conservative for criticality but should be called out when discussing inventory or volume implications.
3. The report should distinguish the current rerun from older `pipe-cross-hu-sweep` results that predate the density-formula update.
