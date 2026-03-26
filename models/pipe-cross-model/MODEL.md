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
- `h_to_u` - Hydrogen-to-uranium atomic ratio for the UO2F2 layer (0.0-50.0, preferred for new studies)
- `uf6_density_g_cm3` - UF6 gas density (1.0e-6-20.0 g/cm³, default: 0.0127)
- `uo2f2_density_g_cm3` - Legacy explicit UO2F2 density override (0.01-20.0 g/cm³, use only when replaying historical dry-fuel parity cases)
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
  h_to_u: [0, 1, 2, 3, 4, 5]
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

When you need to inspect the shared OpenMC builder materials or the MCNP
density forms they produce, use:

```bash
python3 scripts/get_mcnp_density.py uo2f2 -e 20.2 -hu 3
```

The current lightweight solver-to-solver checkpoint for the separation sweep
lives under `certifications/pipe-cross-model/2026-03-24-r1/`.

The staged H/U optimization setup for the original `xz`, `gap = 0` geometry
lives under `studies/pipe-cross-hu-sweep/`.

## Notes

- Default boundaries are reflective in `x/y/z`.
- Default mode is `xz`.
- Pipe models use canonical shared builders: `uf6(...)` and `uo2f2(...)`.
- New studies should specify `h_to_u` and let the model derive `UO2F2` density from the shared ORNL/TM-12292 helper.
- `uo2f2_density_g_cm3` remains only for historical parity/certification reruns where the dry-fuel density was frozen explicitly.
