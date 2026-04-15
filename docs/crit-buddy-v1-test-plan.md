# Experiment: CritBuddy V1 Test Plan

## Objective

Align the V1 parity work on one current material basis and one shared settings
profile, then regenerate comparable OpenMC/MCNP results for the target models.

Update on `2026-04-15`: the shared Monte Carlo settings source now lives in
`critbuddy/solvers/kcode_settings.py`. The parity-style target model
definitions no longer duplicate the `PARTICLES`, `BATCHES`, and `INACTIVE`
defaults locally.

This phase does **not** require `<= 200 pcm` yet. The goal is narrower:

1. use the current shared density model
2. ensure paired cases use the same geometry and `H/U` basis
3. enforce one standard particle/batch/inactive profile
4. produce fresh OpenMC/MCNP comparison tables on that aligned basis

---

## Request Summary

| Field | Value |
|-------|-------|
| Plan ID | `v1-parity-alignment` |
| Workspace | `docs/` plus refreshed study/certification artifacts |
| Models in scope | `centrifuge-unit-cell`, `pipe-cross-model`, `pipe-unit-cell` |
| Setup Date | `2026-04-15` |
| Stage | Ready for implementation |

---

## Background

The current parity artifacts mix two different concerns:

- frozen historical checkpoints under `certifications/`
- the current intended material / settings basis for V1

At the moment:

- `centrifuge-unit-cell` is already using the current shared `H/U` density path
- `pipe-cross-model` certifications are still replaying the legacy explicit
  `UO2F2` density override
- simulation counts are now enforced from the shared
  `critbuddy/solvers/kcode_settings.py` source rather than duplicated per model

This experiment aligns the basis first so later parity analysis is meaningful.

---

## Scope

### In Scope

- Move target parity work to the current shared `UO2F2` density basis
- Make `H/U` explicit where the release basis depends on it
- Refactor target models to consume one shared parity settings profile
- Regenerate paired OpenMC/MCNP artifacts on the aligned basis
- Document the resulting comparison tables and observed residual gaps

### Out of Scope

- Hitting `<= 200 pcm` in this phase
- Rewriting historical certifications in place
- Broad geometry redesign
- Full H/U optimization parity sweep

---

## Fixed Alignment Rules

### 1. Density Basis

- New parity work should use the shared density derivation in:
  - `critbuddy/core/materials/uo2f2_physics.py`
  - `docs/references/materials/uo2f2-density-basis.md`
- For pipe models, avoid `uo2f2_density_g_cm3` in new parity configs unless the
  case is intentionally marked as historical replay.
- Every compared case should state:
  - `enrichment_pct`
  - `h_to_u`
  - derived `UO2F2` bulk density
  - whether the fuel is dry or hydrated

### 2. Geometry Basis

- OpenMC and MCNP comparison cases must use the same documented geometry inputs.
- Each parity package should include a small geometry-basis table before the
  solver comparison table.
- Geometry alignment should be checked before discussing `keff` deltas.

### 3. Settings Basis

- The target parity models should use one shared settings profile for:
  - `PARTICLES`
  - `BATCHES`
  - `INACTIVE`
- Individual parity cases should not define their own counts ad hoc.
- Smoke-test overrides may remain separate from the release parity profile.

---

## Target Basis By Model

### Centrifuge Unit Cell

Release-alignment target:

- model: `centrifuge-unit-cell`
- current shared fuel basis via `h_to_u`
- preserve the canonical parity geometry unless the team explicitly changes it
- keep the current parity air basis

### Pipe Cross Model

Release-alignment target:

- model: `pipe-cross-model`
- reflected `xz` crossing remains the primary parity basis
- replace legacy explicit `6.37 g/cm3` replay configs with explicit `h_to_u`
  configs for new parity runs
- derive `UO2F2` density from the shared helper

### Pipe Unit Cell

Release-alignment target:

- model: `pipe-unit-cell`
- create a true paired OpenMC/MCNP parity package on the same documented basis
- use the same shared settings profile as the other target models

---

## Standard Settings Refactor

Create one shared parity settings source, then point the target model templates
at it. This is now implemented via `critbuddy/solvers/kcode_settings.py`.

Expected implementation shape:

- add one shared settings definition under `critbuddy/solvers/`
- migrate:
  - `models/centrifuge-unit-cell/__init__.py`
  - `models/pipe-cross-model/__init__.py`
  - `models/pipe-unit-cell/__init__.py`
- keep the runner smoke-test override separate from the parity profile

Definition of done for this refactor:

- the three target models no longer duplicate the release parity counts locally
- integration tests assert the shared profile rather than hard-coded per-model
  copies where appropriate

---

## Run Sequence

### Step 1: Freeze The Shared Parity Settings Profile

Purpose: eliminate per-model drift in particle settings before regenerating any
artifacts.

Implementation tasks:

- add the shared parity settings module at
  `critbuddy/solvers/kcode_settings.py`
- update the base template to use it as the default source of
  `PARTICLES/BATCHES/INACTIVE`
- update affected tests

Completion check:

- all three target models resolve the same `PARTICLES`, `BATCHES`, and
  `INACTIVE` values from one source

### Step 2: Refresh Density Basis Inputs

Purpose: ensure new parity cases reflect the current shared material basis.

Implementation tasks:

- define the intended release-basis `h_to_u` for each target case family
- update new parity configs to make `h_to_u` explicit
- remove legacy explicit density from new pipe-cross parity configs
- generate density traceability tables where needed

Completion check:

- `python scripts/audit_certification_density_basis.py` reports new aligned
  pipe-cross artifacts as current shared basis rather than legacy explicit basis

### Step 3: Verify Basis Equivalence Before Solving

Purpose: catch geometry/material mismatches before comparing `keff`.

Required checks per parity package:

- geometry parameter table
- enrichment
- `h_to_u`
- OpenMC fuel density
- MCNP fuel density basis
- settings profile used

Completion check:

- each parity package contains a short basis-verification section

### Step 4: Regenerate Paired OpenMC/MCNP Artifacts

Purpose: produce fresh comparable runs on the aligned basis.

Target outputs:

- refreshed OpenMC exported cases
- rerunnable MCNP case folders
- solver comparison tables for:
  - `centrifuge-unit-cell`
  - `pipe-cross-model`
  - `pipe-unit-cell`

Completion check:

- each target model has one aligned comparison package that can be rerun from
  git

### Step 5: Summarize Residual Gaps

Purpose: record what mismatch remains after basis alignment.

Required summary points:

- whether trends match between solvers
- whether the sign of the bias is stable
- whether the gap shrank, held, or grew relative to older checkpoints
- what remains before a later `200 pcm` push

---

## Success Criteria

- The target parity models use the current shared density basis
- The target parity models use one shared settings profile
- New parity cases explicitly document geometry and `H/U`
- Fresh OpenMC/MCNP comparison tables exist for the aligned basis
- Residual gaps are reported honestly even if they remain above `200 pcm`

---

## Expected Artifacts

### Code / Config

- one shared parity settings module under `critbuddy/solvers/`
- updated target model templates
- updated tests for shared settings behavior
- new or refreshed parity configs using explicit `h_to_u`

### Analysis Outputs

- basis-verification tables for each target parity package
- fresh OpenMC/MCNP comparison tables
- updated certification or study artifacts under new `rN` directories where
  appropriate

### Summary Docs

- updated release summary describing the aligned basis
- updated model certification notes if the blessed checkpoints change

---

## Notes

1. Historical certifications should remain intact; create new aligned artifacts
   instead of rewriting old ones in place.
2. This phase is a basis-alignment phase, not a final acceptance phase.
3. Once this experiment is complete, the repo should be in a much better
   position to pursue a focused `<= 200 pcm` improvement pass.
