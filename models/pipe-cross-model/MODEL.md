# Pipe Cross Model

## Overview

Reflected orthogonal pipe-crossing model for `AD-7` parity work. This model
mirrors the explicit unit-cell style of `centrifuge-unit-cell` and supports
two workbook-aligned crossing patterns.

## Geometry

Supported modes:

- `xz`: one x-directed pipe crossing one z-directed pipe
- `xyz`: mutually orthogonal x/y/z pipes crossing at the origin

Material regions:

- Gas: union of the UF6 core cylinders
- Fuel: union of the annular UO2F2 regions
- Wall: union of the outer cylinders minus fuel
- Moderator: water everywhere else in the reflected box

## Parameters

- `enrichment_pct`
- `cross_mode`
- `pipe_size`
- `pipe_outer_radius_cm`
- `pipe_wall_thickness_cm`
- `gas_core_radius_cm`
- `fuel_outer_radius_cm`
- `uf6_density_g_cm3`
- `uo2f2_density_g_cm3`
- `separation_cm`
- `wall_material`
- `moderator_density_g_cm3`
- `x_boundary_type`
- `y_boundary_type`
- `z_boundary_type`

## Validation Intent

This model is intended to compare against the `AD-7` workbook's crossing cases:

- `Cross Model only x and z cross`
- `Cross Model x,y,z`

with separations including:

- `7.0 cm`
- `6.5 cm`
- `6.0 cm`
- `5.8 cm`

The exact `gap = 0` MCNP reference deck for the reflected `x-z` crossing lives
under `mcnp/reference.inp`, with companion notes in
`mcnp/REFERENCE_ANALYSIS.md`.

For solver-to-solver sanity checks using the current OpenMC builder materials as
the source of truth, use `mcnp/openmc_builder_materials.inp`. Regenerate it
locally with:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python \
  models/pipe-cross-model/mcnp/render_openmc_material_deck.py
```

Quick local validation flow for the exact `xz`, `gap = 0` case:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python \
  run_study.py requests/AD-7/configs/13_cross_model_reference_gap0.yaml

cd models/pipe-cross-model/mcnp
$MCNP_EXECUTABLE i=openmc_builder_materials.inp o=openmc_builder_materials.out tasks 4
```

Compare the OpenMC `k-eff` from `requests/AD-7/runs/13_cross_model_reference_gap0/.../results.csv`
against the MCNP `k-eff` reported in `openmc_builder_materials.out`. This check
isolates geometry plus shared-material parity before reintroducing the
historical MCNP deck materials.

## Notes

- Default boundaries are reflective in `x/y/z`.
- Default mode is `xz`.
- Pipe models use canonical shared builders: `uf6(...)` and `uo2f2(..., h_to_u=0.0, ...)`.
- Both fissile material densities are explicit model inputs.
