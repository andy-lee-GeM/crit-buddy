# Criticality Model Handoff Template

## Purpose

This document explains the canonical criticality model used by the RE team for
engineering evaluation of a specific physical system.

It is intended to help a criticality safety reviewer understand:

- what the model represents
- what inputs engineers are allowed to change
- what assumptions are fixed in the template
- what materials and solver setup were used
- how the OpenMC model was benchmarked against MCNP
- how the model has been used by engineers
- what limitations apply to the model

This document is a model review and traceability package. It is not the final
licensing or NCSE deliverable.

## Model Overview

### Physical system

Describe the physical system in plain engineering terms.

Include:

- what equipment or configuration the model represents
- what the major regions are
- what the boundary conditions represent physically
- what design questions the model is intended to support

### Geometry summary

Summarize the geometry at a level that a reviewer can follow without reading
code.

Include:

- principal dimensions
- region definitions
- coordinate conventions
- reflective or vacuum boundaries

If useful, include a sketch or labeled section view.

## Configurable Parameters

This section should clearly define what engineers are allowed to vary as part
of the model.

For each parameter, list:

- parameter name
- physical meaning
- units
- baseline value
- normal sweep range
- comments on intended use

Suggested table:

| Parameter | Meaning | Units | Baseline | Normal range | Notes |
| --- | --- | --- | --- | --- | --- |
| `fill_z_cm` | Fuel fill height | cm | `30` | `10-50` | Used in engineering sweeps |

This is one of the most important sections in the handoff because it tells the
reviewer exactly what engineers have been changing in practice.

## Modeling Assumptions

Document the assumptions built into the template model.

This should include:

- geometry simplifications
- boundary condition assumptions
- source assumptions
- material idealizations
- any parity-preserving choices made to match the MCNP reference model

This section should answer: "What is fixed in this model before any engineer
starts sweeping parameters?"

## Material Definitions

Describe the materials used in the model and where their basis comes from.

Include:

- shared library materials used directly
- generated fissile or process materials
- density basis
- isotopic or compositional basis
- enrichment and hydration basis where relevant
- any special-case materials used only for parity

Reference basis documents here rather than duplicating long derivations.

## Solver / Analysis Setup

Describe how the model is run in OpenMC and how results are generated.

Include:

- model execution path
- solver environment or version if relevant
- particle, batch, and inactive/active cycle settings
- source definition approach
- boundary treatment
- output artifacts produced by the run
- reporting or post-processing used to summarize the results

This section should make it clear what was actually solved.

## Benchmarking

This section should show why the OpenMC model is credible as an engineering
tool.

The goal is to demonstrate that the OpenMC template reproduces the intended
MCNP reference behavior closely enough for engineering exploration.

Include:

- a short description of the MCNP reference basis
- the cases used for comparison
- the OpenMC / MCNP comparison table
- maximum delta keff
- any known systematic bias
- a short statement explaining why the benchmark result was accepted

Suggested table:

| Case | MCNP keff | OpenMC keff | MCNP std | OpenMC std | Delta keff |
| --- | ---: | ---: | ---: | ---: | ---: |
| `case_1` | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |

This section should read as benchmarking evidence, not just a pointer to the
certification directory.

## Engineering Use of the Model

This section explains how systems engineers have actually been using the model.

It can start as a placeholder if needed.

Include:

- what design studies have used this model
- what engineering questions it has been used to answer
- what decisions it has informed
- what kinds of sweeps engineers commonly run

Suggested placeholder:

"To date, systems engineers have used this model primarily for early design
space exploration, including geometry sweeps, material sensitivity checks, and
bounding criticality evaluations. This section will be expanded with specific
study references as the handoff package matures."

## Parameter Sensitivity / Lookup Sweeps

This section should summarize simple one-parameter sweeps that help a reviewer
understand how sensitive `k-effective` is to individual inputs.

The intent is not to present the full design study. The intent is to provide
clear lookup-style guidance showing how the model responds when one parameter is
varied while others are held fixed.

These tables are useful for:

- identifying the approximate max-keff region
- showing which parameters are most sensitive
- giving engineers a starting point for future studies
- helping the reviewer understand model behavior without reading raw run output

For each sweep, include:

- parameter varied
- fixed baseline for all other inputs
- sweep values
- resulting keff and uncertainty
- short interpretation of where max-keff occurs

Suggested subsection examples:

### H/U sweep

Use this subsection to show how `k-effective` changes with `H/U` and to
identify the approximate optimum or peak-reactivity region.

Suggested table:

| H/U | Density (g/cm3) | keff | std | Notes |
| ---: | ---: | ---: | ---: | --- |
| 0 | 0.00000 | 0.00000 | 0.00000 | |

### Other single-parameter sweeps

Use similar tables for any parameter that has strong effect on reactivity, such
as:

- fill height
- separation distance
- moderator density
- enrichment
- wall material or wall thickness

Each table should end with a short statement summarizing the sensitivity trend.

## Limitations

State clearly where the model should and should not be used.

Include:

- known OpenMC / MCNP differences
- idealizations that matter to interpretation
- parameters or regimes that have not been benchmarked
- situations that would require model revision before reuse
- decisions that still require direct criticality safety judgment

This section is where the reviewer should learn how to treat the model with the
right amount of caution.

## Appendix

### A. Reference MCNP model

Provide the path to the reference MCNP input deck(s) and any companion notes
needed to interpret them.

### B. Reference OpenMC model

Provide the path to the reference OpenMC `model.py` used as the canonical
implementation.

### C. Material library

Provide the path to the shared material library, generated material helpers, and
any supporting material basis documents.

### D. Supporting benchmark and sweep artifacts

List the concrete files that support the benchmarking and sensitivity sections,
such as:

- comparison tables
- study configs
- exported OpenMC cases
- MCNP outputs
- summary reports
- plots
