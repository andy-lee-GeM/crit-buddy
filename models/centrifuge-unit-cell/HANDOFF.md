# Centrifuge Unit Cell Handoff

## Purpose

This document is the reviewer-facing handoff for the canonical
`centrifuge-unit-cell` model used in crit-buddy.

Its purpose is to help a criticality safety reviewer understand:

- what physical system the model represents
- what parameters engineers are allowed to change
- what assumptions are fixed in the template
- how materials are defined
- how the model is run in OpenMC
- how the OpenMC implementation compares against the MCNP reference basis
- how engineers have used the model so far
- how sensitive `k-effective` is to the current one-parameter sweep data

This handoff supports engineering review and traceability. It is not the final
licensed MCNP deliverable.

## Model Overview

The centrifuge unit cell model represents a single cylindrical centrifuge vessel
inside a reflective square unit cell. The current maintained model is the
cleaned canonical version of the earlier Steven film work and is intended to be
the baseline OpenMC implementation for parity checks and engineering sweeps.

The physical regions are:

- `UO2F2` fuel inside the inner vessel radius up to the fill height
- gas headspace above the fill level inside the vessel
- a water annulus around the vessel contents
- a steel wall and steel end caps
- internal and external air regions within the reflected unit cell

For the current benchmarked basis:

- inner fuel radius = `11.70 cm`
- water film thickness = `1.0 cm`
- wall thickness = `0.3175 cm`
- vessel height = `100.0 cm`
- fill sweep = `10, 20, 30, 40, 50 cm`
- reflective boundaries are used in `x`, `y`, and `z`

The model is intended to answer questions such as:

- how reactivity changes with fill height
- how sensitive the unit cell is to vessel geometry changes
- how the maintained OpenMC implementation tracks the cleaned MCNP reference

## Configurable Parameters

All parameters below are user-configurable through the standard model YAML
interface. The table distinguishes template defaults from the frozen benchmark
basis and from the way engineers are expected to use the model.

| Parameter | Meaning | Units | Template default | Typical use | Benchmark / notes |
| --- | --- | --- | --- | --- | --- |
| `enrichment_pct` | U-235 weight percent in the `UO2F2` fuel | `%` | `20.2` | Fissile sensitivity studies | Benchmark uses `20.2` |
| `h_to_u` | Hydrogen-to-uranium atomic ratio for the fuel | - | `5.0` | Chemistry / moderation sensitivity studies | Benchmark uses `5.0` |
| `inner_radius_cm` | Inner vessel radius / fuel radius | `cm` | `11.70` | Vessel geometry sweeps | Benchmark uses `11.70` |
| `water_film_thickness_cm` | Water film thickness outside the fuel region | `cm` | `1.0` | Geometry / moderation sweeps | Benchmark uses `1.0` |
| `wall_thickness_cm` | Steel wall thickness, also used for end caps | `cm` | `0.3175` | Geometry sweeps | Benchmark uses `0.3175` |
| `vessel_height_cm` | Total vessel height | `cm` | `100.0` | Geometry sweeps | Benchmark uses `100.0` |
| `fill_height_cm` | Fuel fill height measured from vessel bottom | `cm` | `20.0` | Primary fill-height sweep parameter | Frozen benchmark covers `10.0`, `20.0`, `30.0`, `40.0`, `50.0` |
| `source_z_cm` | Preferred MCNP-style source z location | `cm` | `10.0` | Usually fixed near the fuel region for parity work | Benchmark uses `10.0` |
| `x_boundary_type` | Boundary at `x` min / max | - | `reflective` | Usually fixed to the unit-cell basis | Benchmark uses `reflective` |
| `y_boundary_type` | Boundary at `y` min / max | - | `reflective` | Usually fixed to the unit-cell basis | Benchmark uses `reflective` |
| `z_boundary_type` | Boundary at `z` min / max | - | `reflective` | Usually fixed to the unit-cell basis | Benchmark uses `reflective` |

## Modeling Assumptions

- The current OpenMC model follows the cleaned canonical geometry intent rather
  than reproducing the malformed overlapping outer-air cells in the older MCNP
  decomposition.
- Fuel, wall, and water use the shared library / builder path used elsewhere in
  the repo.
- Air uses the shared `centrifuge_air` material so the OpenMC parity basis
  preserves the legacy MCNP air card instead of the earlier humid-air regression.
- End-cap thickness is tied to `wall_thickness_cm`.
- The reflected `x`, `y`, and `z` boundaries represent a repeated unit-cell
  approximation rather than an isolated finite system.
- The OpenMC source is clamped into the fuel region when needed so the low-fill
  cases remain physically meaningful.
- The model is a static transport model with no burnup, depletion, or absorber
  credit.

## Material Definitions

The centrifuge unit cell uses shared material builders from
`critbuddy/core/materials/` so the benchmark and future studies stay on one
material basis.

Static shared materials used directly in this model:

- `stainless_steel_316` for the wall and end caps
- `water` for the moderator film
- `centrifuge_air` for the legacy parity air basis

Generated process material used in this model:

- `uo2f2(enrichment_pct, h_to_u, density)` for the fuel region

Material basis for each region:

- `UO2F2` fuel is created through the shared fissile-material path using
  enrichment and `h_to_u`.
- The water region uses the shared `water()` builder with the standard density
  of `1.0 g/cm3` in the current benchmark.
- The wall uses shared stainless steel rather than a model-local composition.
- The air regions use `centrifuge_air`, which is a parity-preserving material
  that matches the legacy MCNP air card more closely than the older humid-air
  implementation.

Current material references for this model:

- `critbuddy/core/materials/builders.py`
- `critbuddy/core/materials/material_specs.py`
- `critbuddy/core/materials/uo2f2_physics.py`
- `docs/references/materials/README.md`
- `docs/references/materials/uo2f2-density-basis.md`

## Solver / Analysis Setup

The OpenMC implementation lives in `openmc/model.py` under this model folder.
It builds a parameterized unit-cell geometry and writes standard OpenMC exported
case files for each run.

Current solver setup:

- run mode: eigenvalue
- particles per batch: `4800`
- total batches: `200`
- inactive batches: `50`
- source: point source with z position clamped into the fuel region

For each case, crit-buddy can preserve:

- `materials.xml`
- `geometry.xml`
- `settings.xml`
- `results.csv`
- `REPORT.md`
- summary plots

The frozen parity checkpoint for this model is driven from:

- `certifications/centrifuge-unit-cell/2026-03-30-r1/openmc/study.yaml`

That checkpoint stores the frozen OpenMC case exports and the rerunnable MCNP
case directories used for comparison.

## Benchmarking

The benchmark basis for this handoff is the frozen fill-height sweep under
`certifications/centrifuge-unit-cell/2026-03-30-r1/`.

Reference basis:

- physical basis: single cylindrical centrifuge vessel inside a reflective
  square unit cell
- reference deck: `models/centrifuge-unit-cell/mcnp/model.inp`
- OpenMC parity config:
  `certifications/centrifuge-unit-cell/2026-03-30-r1/openmc/study.yaml`

Compared cases:

- `fill_10`
- `fill_20`
- `fill_30`
- `fill_40`
- `fill_50`

Benchmark comparison:

| Case | MCNP keff | OpenMC keff | MCNP std | OpenMC std | Delta keff |
| --- | ---: | ---: | ---: | ---: | ---: |
| `fill_10` | 0.99269 | 0.99000 | 0.00096 | 0.00103 | -0.00269 |
| `fill_20` | 1.20945 | 1.20785 | 0.00093 | 0.00104 | -0.00160 |
| `fill_30` | 1.30067 | 1.29851 | 0.00084 | 0.00106 | -0.00216 |
| `fill_40` | 1.35134 | 1.34520 | 0.00095 | 0.00111 | -0.00614 |
| `fill_50` | 1.38045 | 1.37936 | 0.00089 | 0.00105 | -0.00109 |

Benchmark observations:

- Maximum absolute `Delta keff` in the frozen checkpoint is `0.00614`.
- The current discrepancy is small and uniformly negative across the fill sweep:
  OpenMC is lower than MCNP in all five benchmarked cases.
- The trend with fill height is reproduced cleanly in both solvers: increasing
  fill height increases `k-effective` across the sampled range.
- The `fill_10` case uses a manual MCNP source adjustment to keep the source
  inside the fuel region.
- The shared `centrifuge_air` material removed the earlier humid-air regression
  from the OpenMC parity baseline.

Benchmark interpretation:

The current benchmark is sufficient for the model's intended role as an
engineering exploration tool for relative trend evaluation and early design
screening. The remaining negative bias is explicit and bounded in the current
fill sweep. Final safety basis work should still be translated into the
consultant's qualified MCNP workflow and verified there.

## Engineering Use of the Model

To date, this model has mainly been used as:

1. A solver-to-solver parity model for the canonical single-centrifuge unit
   cell.
2. A starting point for early vessel-geometry exploration, especially fill
   height, vessel dimensions, and related bounding unit-cell studies.

In practice, systems engineers can use this model as a starting point for:

- fill-height sensitivity studies
- vessel radius and wall-thickness sweeps
- water-film thickness studies
- enrichment studies
- early bounding evaluations on reflective unit-cell configurations

The current published study history is still limited. This handoff should be
treated as the baseline package for future design-space studies built from the
same canonical model.

## Parameter Sensitivity / Lookup Sweeps

This section collects simple one-parameter sweep data that can serve as a
lookup table for future engineering work.

### Fill-height sweep

Fixed basis:

- model: `centrifuge-unit-cell`
- enrichment: `20.2 wt%`
- `H/U = 5.0`
- inner radius: `11.70 cm`
- water film thickness: `1.0 cm`
- wall thickness: `0.3175 cm`
- vessel height: `100.0 cm`
- source z: `10.0 cm`
- boundaries: reflective in `x`, `y`, and `z`

Results:

| Fill height (cm) | OpenMC keff | OpenMC std | MCNP keff | Delta keff |
| ---: | ---: | ---: | ---: | ---: |
| 10.0 | 0.99000 | 0.00103 | 0.99269 | -0.00269 |
| 20.0 | 1.20785 | 0.00104 | 1.20945 | -0.00160 |
| 30.0 | 1.29851 | 0.00106 | 1.30067 | -0.00216 |
| 40.0 | 1.34520 | 0.00111 | 1.35134 | -0.00614 |
| 50.0 | 1.37936 | 0.00105 | 1.38045 | -0.00109 |

Interpretation:

- `k-effective` increases monotonically with fill height across the sampled
  range.
- The `50 cm` case is the most reactive point in the frozen fill sweep.
- The benchmark and lookup sweep are the same dataset in the current handoff,
  since the fill-height sweep is both the parity basis and the clearest
  existing one-parameter sensitivity study.

## Limitations

- The frozen benchmark covers the reflective unit-cell basis only.
- The current handoff does not include independent benchmark sweeps for radius,
  wall thickness, water-film thickness, or boundary-condition changes.
- The `fill_10` parity case requires a manual MCNP source adjustment.
- The model uses idealized repeated-cell boundaries rather than a plant-specific
  finite system.
- The current published lookup data are strongest for fill height; other design
  parameters still need similarly curated sweep data if they are going to be
  used routinely by engineers.
- Final safety conclusions, licensing work, and qualified V&V still belong in
  the consultant's MCNP workflow.

## Appendix

### Reference MCNP model

- [model.inp](mcnp/model.inp)

### Reference OpenMC model

- [model.py](openmc/model.py)
- [example_config.yaml](openmc/example_config.yaml)
- [__init__.py](__init__.py)

### Material library

- [builders.py](../../critbuddy/core/materials/builders.py)
- [material_specs.py](../../critbuddy/core/materials/material_specs.py)
- [uo2f2_physics.py](../../critbuddy/core/materials/uo2f2_physics.py)
- [README.md](../../docs/references/materials/README.md)
- [uo2f2-density-basis.md](../../docs/references/materials/uo2f2-density-basis.md)

### Supporting benchmark artifacts

- [results.md](../../certifications/centrifuge-unit-cell/2026-03-30-r1/results.md)
- [study.yaml](../../certifications/centrifuge-unit-cell/2026-03-30-r1/openmc/study.yaml)
- [REPORT.md](../../certifications/centrifuge-unit-cell/2026-03-30-r1/openmc/results/REPORT.md)
