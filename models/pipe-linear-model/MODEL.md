# Pipe Linear Model

## Overview

Reflected single-pipe linear model used for `AD-7` parity checks. The model is
intentionally built in the same style as `centrifuge-unit-cell`: explicit CSG
surfaces, explicit reflective boundary planes, and a compact set of material
regions.

## Geometry

- Gas: `UF6` inside `r < gas_core_radius_cm`
- Fuel: annular `UO2F2` from `gas_core_radius_cm` to `fuel_outer_radius_cm`
- Wall: pipe wall from `fuel_outer_radius_cm` to `pipe_outer_radius_cm`
- Moderator: water everywhere else in the reflected box
- Axial extent: pipe extends through the full `axial_height_cm`

The default geometry is a reflected `NPS 4` pipe with:

- outer radius: `5.715 cm`
- wall thickness: `0.3048 cm`
- gas core radius: `4.4102 cm`
- fuel outer radius: `5.4102 cm`
- reflected separation: `6.4 cm`

## Parameters

- `enrichment_pct`
- `pipe_size`
- `pipe_outer_radius_cm`
- `pipe_wall_thickness_cm`
- `gas_core_radius_cm`
- `fuel_outer_radius_cm`
- `uf6_density_g_cm3`
- `uo2f2_density_g_cm3`
- `separation_cm`
- `axial_height_cm`
- `wall_material`
- `moderator_density_g_cm3`
- `x_boundary_type`
- `y_boundary_type`
- `z_boundary_type`

## Validation Intent

This model is intended to compare against the `AD-7` workbook's reflected
single-pipe cases such as:

- `6.4 cm separation`
- `6.0 cm separation`

## Notes

- Default boundaries are reflective in `x/y/z`.
- Pipe models use canonical shared builders: `uf6(...)` and `uo2f2(..., h_to_u=0.0, ...)`.
- Both fissile material densities are explicit model inputs.
