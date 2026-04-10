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
- `mcnp/template.inp`: active MCNP template used for config-driven study runs
- `mcnp/model.py`: MCNP render helper that derives material cards from the shared builders
- `mcnp/model.inp`: canonical MCNP deck for the `20 wt%`, `H/X = 100` single-case parity check
- `mcnp/REFERENCE_ANALYSIS.md`: geometry/material notes for the canonical MCNP deck

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
- The canonical MCNP deck currently covers one benchmark point:
  `20 wt%`, `H/X = 100`, `13.88 cm` fuel radius, `100 cm` water reflector,
  vacuum outer boundary.
- The templated MCNP path uses the same shared `H/X -> H/U -> density` basis as
  the OpenMC model, so study sweeps can be rerun with
  `python run_study.py ... --solver mcnp`.
- To regenerate the shared MCNP-oriented fuel density / nuclide table for that
  point, use:

```bash
python scripts/get_mcnp_density.py uo2f2 --no-default-sweeps -e 20.0 --h-to-u 20.204171182632887
```
