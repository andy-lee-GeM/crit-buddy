# Centrifuge Unit Cell

## Overview

This model represents a single cylindrical centrifuge vessel inside a
reflective square unit cell. It is the canonical cleaned version of the model
previously developed under the Steven film naming and is intended to be the
shared baseline for OpenMC development and MCNP reference runs.

## Files

- `openmc/model.py`: active OpenMC implementation used for development and
  config-driven studies.
- `mcnp/model.inp`: canonical MCNP deck for manual reference runs.

## Geometry Summary

- Fuel region: `r < 11.70 cm`
- Water film: `11.70 < r < 12.70 cm`
- Steel wall: `12.70 < r < 13.0175 cm`
- Steel end caps close the vessel axially
- Canonical parity case uses reflective square unit-cell boundaries in
  `x`, `y`, and `z`

## Modeling Assumptions

- The canonical MCNP deck collapses the original overlapping outer-air cells
  into one clean non-overlapping region.
- The OpenMC model follows the cleaned canonical geometry intent rather than
  reproducing the malformed original cell decomposition.
- Fuel, wall, and water now follow the shared config-to-library material path
  used elsewhere in the repo.
- Air now uses the shared `centrifuge_air` library material, which preserves
  the legacy MCNP card for parity work.
- OpenMC is the primary development implementation; MCNP is maintained as the
  canonical reference deck for downstream use.

## Validation

- The current lightweight cross-solver checkpoint lives under
  `certifications/centrifuge-unit-cell/2026-03-30-r1/` and includes the
  frozen `openmc/model.py` source snapshot alongside the exported cases.
- Model geometry and material construction are covered by the test suite.
- Additional benchmark-style validation can be added as separate studies.

## History

This model was previously tracked in the repo under the Steven film naming.
Legacy exploratory decks, runs, and archived work remain under
`workbench/centrifuge-unit-cell/`.
