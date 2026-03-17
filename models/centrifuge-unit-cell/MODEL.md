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
- OpenMC is the primary development implementation; MCNP is maintained as the
  canonical reference deck for downstream use.

## Validation

- Cross-solver comparison is documented in
  `studies/centrifuge-unit-cell-parity/`.
- Model geometry and material construction are covered by the test suite.
- Additional benchmark-style validation can be added as separate studies.

## History

This model was previously tracked in the repo under the Steven film naming.
Legacy exploratory decks, runs, and archived work remain under
`workbench/centrifuge-unit-cell/`.
