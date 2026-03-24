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

- `enrichment_pct` - U-235 weight percent enrichment (0.1-100.0%, default: 20.2)
- `cross_mode` - Crossing pattern: `xz` or `xyz` (default: `xz`)
- `pipe_size` - Standard NPS size or `custom` (default: `custom`)
- `pipe_outer_radius_cm` - Outer pipe radius for custom sizing (0.5-50.0 cm, default: 5.715)
- `pipe_wall_thickness_cm` - Pipe wall thickness for custom sizing (0.05-5.0 cm, default: 0.3048)
- `gas_core_radius_cm` - Radius of central UF6 gas core (0.05-50.0 cm, default: 4.4102)
- `fuel_outer_radius_cm` - Outer radius of annular UO2F2 layer (0.05-50.0 cm, default: 5.4102)
- `uf6_density_g_cm3` - UF6 gas density (1.0e-6-20.0 g/cm³, default: 0.0127)
- `uo2f2_density_g_cm3` - Dry UO2F2 density (0.01-20.0 g/cm³, default: 6.37)
- `separation_cm` - Edge-to-edge separation to reflected neighbors (0.0-100.0 cm, default: 7.0)
- `wall_material` - Pipe wall material: `aluminum` or `ss304` (default: `aluminum`)
- `moderator_density_g_cm3` - Water moderator density (0.01-2.0 g/cm³, default: 1.0)
- `x_boundary_type` - Boundary at x-min/max: `reflective` or `vacuum` (default: `reflective`)
- `y_boundary_type` - Boundary at y-min/max: `reflective` or `vacuum` (default: `reflective`)
- `z_boundary_type` - Boundary at z-min/max: `reflective` or `vacuum` (default: `reflective`)

## Config File Usage

This model uses the standard config-driven workflow. Create a YAML config file:

```yaml
model: pipe-cross-model
name: Your Study Name

params:
  cross_mode: xz
  enrichment_pct: 20.19
  separation_cm: [0.0, 5.8, 6.0, 6.5, 7.0]  # List for parameter sweep
  # ... other parameters
```

Run with:

```bash
python3 run_study.py path/to/config.yaml
```

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
python3 models/pipe-cross-model/mcnp/render_openmc_material_deck.py
```

Quick local validation flow for the exact `xz`, `gap = 0` case:

```bash
python3 run_study.py path/to/gap0_config.yaml

cd models/pipe-cross-model/mcnp
$MCNP_EXECUTABLE i=openmc_builder_materials.inp o=openmc_builder_materials.out tasks 4
```

Compare the OpenMC `k-eff` from your one-case run `results.csv` against the
MCNP `k-eff` reported in `openmc_builder_materials.out`. This check isolates
geometry plus shared-material parity before reintroducing the historical MCNP
deck materials.

The current lightweight solver-to-solver checkpoint for the separation sweep
lives under `certifications/pipe-cross-model/2026-03-24-r1/`.

## Notes

- Default boundaries are reflective in `x/y/z`.
- Default mode is `xz`.
- Pipe models use canonical shared builders: `uf6(...)` and `uo2f2(..., h_to_u=0.0, ...)`.
- Both fissile material densities are explicit model inputs.
