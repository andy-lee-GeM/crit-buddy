# UO2F2 Sphere Benchmark

## Overview

This model represents a homogeneous `UO2F2-H2O` fuel sphere surrounded by a
water reflector. It is intended for benchmark-style moderation studies where
the reference basis is expressed in `H/X` but the shared material builders use
`H/U`.

## Files

- `openmc/model.py`: active OpenMC implementation used for config-driven runs
- `openmc/example_config.yaml`: copy-pasteable config showing the user-facing inputs
- `openmc/visualization_config.yaml`: single-case preview config for `--validate`

## User Inputs

- `enrichment_pct`
- `h_over_x` or `h_to_u`
- `sphere_radius_cm`
- `reflector_thickness_cm`
- `reflector_density_g_cm3`
- `outer_boundary_type`

Exactly one moderation input should be provided:

- `h_over_x`: paper-facing hydrogen-to-fissile ratio
- `h_to_u`: shared-library hydrogen-to-uranium ratio

## Modeling Assumptions

- The fissile region is a homogeneous `UO2F2-H2O` mixture built through the
  shared `uo2f2(...)` material constructor.
- The reflector is homogeneous light water.
- No structural materials are included.
- The outer boundary defaults to vacuum; a sufficiently thick water shell is
  used to approximate full water reflection studies.

## Notes

- Benchmark studies should generally sweep `h_over_x` so the results map
  directly back to the paper tables.
- The template derives the exact companion `H/U` internally from enrichment and
  the `U-235` atom fraction.
