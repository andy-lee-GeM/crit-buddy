# CritBuddy V1 Release Certification Plan

## Purpose

CritBuddy V1 needs a release gate that is stricter than the current lightweight
certification checkpoints. The existing checkpoints are useful frozen artifacts,
but they do not yet prove the three release criteria below:

1. `centrifuge-unit-cell` agrees with MCNP within `200 pcm`
2. piping models agree with MCNP within `200 pcm`
3. the `H/U` search agrees with MCNP on the peak moderation point and on
   eigenvalues within `200 pcm`

Execution sequencing for the basis-alignment phase lives in
`docs/crit-buddy-v1-test-plan.md`.

## Current Status

| Release criterion | Current evidence | Status |
| --- | --- | --- |
| Centrifuge parity within `200 pcm` | `certifications/centrifuge-unit-cell/2026-03-30-r1/results.md` preserves a five-point fill sweep, but the worst delta is `-614 pcm` at `fill_40` | NOT MET |
| Pipe parity within `200 pcm` | `certifications/pipe-cross-model/2026-03-30-r1/results.md` preserves the reflected `xz` crossing sweep, but the worst delta is `+988 pcm` at `sep_5.8` | NOT MET |
| Single-pipe parity against MCNP | `models/pipe-unit-cell/MODEL.md` explicitly says there is no MCNP comparison for the single-pipe model today | MISSING |
| `H/U` search parity against MCNP | `studies/pipe-cross-hu-sweep/report.md` is OpenMC-only and documents the current shared density basis, with a sampled peak at `H/U = 3.5` | MISSING |

## What Certifications Already Handle

The current `certifications/` structure is still useful and should remain the
place where fixed parity checkpoints are frozen. A certification is the right
artifact for:

- the exact OpenMC source snapshot used for a parity comparison
- the exact study config and exported OpenMC cases
- the rerunnable MCNP `input.inp` and `out` files
- a short comparison table for a fixed set of agreed cases

## What Certifications Do Not Handle By Themselves

The current certifications do not provide a sufficient V1 release gate on their
own:

- They preserve whatever density basis was used at the time, including legacy
  explicit densities.
- They do not assert a pass/fail release threshold such as `<= 200 pcm`.
- They do not cover the single-pipe model today.
- They do not cover an end-to-end `H/U` search in both solvers.

The `H/U` search is especially important to separate conceptually:

- The optimization sweep itself belongs under `studies/` because it is a search.
- The fixed comparison points selected from that search can then be frozen under
  `certifications/` once the basis is agreed.

## Density-Basis Check

Before blessing any new V1 checkpoint, run:

```bash
python scripts/audit_certification_density_basis.py
```

This audit distinguishes two cases:

- `current_shared_basis`: the frozen `materials.xml` fuel density matches the
  current shared `UO2F2` density path
- `legacy_explicit_basis`: the checkpoint is replaying an older explicit density
  override rather than the current shared density calculation

Follow-up checks for each release candidate:

1. Confirm whether the checkpoint is supposed to preserve a historical basis or
   certify the current shared basis.
2. If it is supposed to certify the current shared basis, reject any
   `legacy_explicit_basis` finding and regenerate the checkpoint from a config
   that uses `h_to_u`.
3. For `H/U` studies, export the density traceability table with
   `scripts/uo2f2_density_hu_sweep.py` and preserve it with the study results.
4. Compare the frozen OpenMC `materials.xml` fuel density with the density
   implied by the matching MCNP deck before blessing the checkpoint.

## Minimum V1 Test Plan

### 1. Centrifuge

- Create a new `centrifuge-unit-cell` certification under a new `rN` directory.
- Keep the same fixed geometry basis unless the team explicitly changes it.
- Require every sampled case to be within `200 pcm`.
- Keep the current density basis explicit in the release notes:
  `enrichment_pct = 20.2`, `h_to_u = 5.0`, water `1.0 g/cm3`, legacy
  `centrifuge_air`.

### 2. Piping

- Add a new `pipe-unit-cell` MCNP parity package. This is currently missing.
- Add a new `pipe-cross-model` certification for the reflected `xz` crossing on
  the agreed release density basis.
- Decide explicitly whether `xyz` is in V1 scope. If yes, it needs its own MCNP
  comparison cases; if no, say so in the release notes.
- Do not use the legacy explicit `6.37 g/cm3` `UO2F2` density for a release
  certification unless the team intentionally wants to certify that historical
  basis instead of the current shared one.

### 3. H/U Search

- Keep the search sweep under `studies/`.
- Run the same `H/U` grid in both OpenMC and MCNP on the same geometry and
  density basis.
- Compare at least the local peak neighborhood, not just one point, so the team
  can tell whether both solvers agree on the same peak band.
- Freeze the final compared peak-point evidence in a new certification or in a
  release summary that references the study outputs.

## Recommended Release Outputs

For a clean V1 decision, the repo should contain:

- a new centrifuge certification that passes the `200 pcm` threshold
- a new pipe-unit-cell certification or equivalent MCNP parity package
- a new pipe-cross-model certification that passes the `200 pcm` threshold on
  the intended release density basis
- an `H/U` parity study package with density traceability and solver agreement
  on the peak moderation region
- a short release summary that records which artifacts satisfy criteria `1-3`

## Decision Rule

CritBuddy V1 should not claim these items are certified until all three are
true:

- the frozen density basis is verified and intentional
- the target model comparisons are within `200 pcm`
- the `H/U` search has been repeated in both solvers on the same basis
