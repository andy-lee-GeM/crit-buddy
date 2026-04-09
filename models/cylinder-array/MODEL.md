# Cylinder Array

## Overview

This model represents a finite array of closed centrifuge-style cylinders using
the maintained `centrifuge-unit-cell` vessel geometry as the reusable building
block. The model is intended for finite arrangement studies where the engineer
specifies explicit cylinder counts and a uniform wall-to-wall gap.

## Files

- `HANDOFF.md`: reviewer-facing engineering handoff covering current model
  status, validation, engineering use, and certification gaps.
- `openmc/model.py`: active OpenMC implementation used for development and
  config-driven studies.
- `openmc/example_config.yaml`: copy-pasteable OpenMC study config showing the
  intended user-facing array inputs.
- `openmc/visualization_config.yaml`: single-case preview config used for
  `--validate` geometry renders.

## Geometry Summary

- Reused vessel geometry inputs:
  - `inner_radius_cm`
  - `water_film_thickness_cm`
  - `wall_thickness_cm`
  - `vessel_height_cm`
  - `fill_height_cm`
- Array inputs:
  - `num_cylinders_x`
  - `num_cylinders_y`
  - `num_cylinders_z`
  - `wall_to_wall_gap_cm`
  - `edge_moderator_thickness_cm`
- User-facing axes:
  - `x`: horizontal
  - `y`: vertical
  - `z`: depth
- Internal implementation keeps the cylinder axis aligned with the OpenMC
  z-axis and remaps user `y` and `z` accordingly.

## Modeling Assumptions

- Adjacent cylinders use a uniform edge-to-edge gap in the horizontal, depth,
  and vertical directions.
- A water moderator shell surrounds the finite array before the outer vacuum or
  reflective boundary.
- The shell thickness is controlled by `edge_moderator_thickness_cm` and
  defaults to `50 cm`.
- Materials follow the maintained centrifuge model:
  - UO2F2 fuel from the shared builder path
  - stainless steel 316 wall
  - water annulus
  - external water shell
  - shared `centrifuge_air`

## Boundary Conditions

- Default boundary setup is vacuum in `x`, `y`, and `z` for finite-array
  leakage studies.
- Reflective boundaries remain available for sensitivity or bounding cases.

## Validation

- Geometry and material construction are covered by the integration test
  `tests/integration/models/test_cylinder_array.py`.
- Visualization can be generated with
  `models/cylinder-array/openmc/visualization_config.yaml`.
- The current reviewer-facing handoff is `models/cylinder-array/HANDOFF.md`.
- The model has completed production engineering use in `requests/CB-17/`.
- No frozen OpenMC/MCNP certification checkpoint exists yet under
  `certifications/cylinder-array/`.

## History

- The model was introduced as the finite-array extension of the maintained
  `centrifuge-unit-cell` vessel basis.
- The first completed published engineering workflow for this model family is
  `requests/CB-17/`.
- As of `2026-04-05`, the model has a formal handoff document but does not yet
  have a blessed solver-to-solver certification checkpoint.
