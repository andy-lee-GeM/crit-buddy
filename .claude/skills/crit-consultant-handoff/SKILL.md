---
name: crit-consultant-handoff
description: Create or update a consultant-facing criticality model handoff document for crit-buddy. Use when asked to explain a canonical model in depth for a criticality safety reviewer, package OpenMC/MCNP benchmarking evidence, document configurable parameters and assumptions, summarize how engineers use the model, or include lookup-style one-parameter sensitivity sweeps such as H/U vs keff.
---

# Skill: Crit Consultant Handoff

Create a reviewer-facing handoff document for a canonical crit-buddy model.

This document is separate from `models/<model>/MODEL.md`.

Keep `MODEL.md` as the compact internal model description. Put the fuller
reviewer package in:

- `models/<model>/HANDOFF.md`

Use the handoff to explain the model clearly to a criticality safety expert who
may not trust OpenMC by default and will want to see concrete parity evidence.

## Goals

The handoff document should help a reviewer understand:

- what physical system the model represents
- what parameters engineers can change
- what assumptions are fixed in the template
- what materials are used and where they come from
- how the model is run in OpenMC
- how OpenMC was benchmarked against MCNP
- how engineers have used the model so far
- how sensitive `k-effective` is to major one-parameter sweeps
- where the model should and should not be used

## Required Sections

Use this section order unless the user asks for something else:

1. `Purpose`
2. `Model Overview`
3. `Configurable Parameters`
4. `Modeling Assumptions`
5. `Material Definitions`
6. `Solver / Analysis Setup`
7. `Benchmarking`
8. `Engineering Use of the Model`
9. `Parameter Sensitivity / Lookup Sweeps`
10. `Limitations`
11. `Appendix`

## Appendix Contents

Include these appendix subsections when the artifacts exist:

- `Reference MCNP model`
- `Reference OpenMC model`
- `Material library`
- `Supporting benchmark and sweep artifacts`

Use absolute repo paths when referencing concrete files in generated responses or
notes.

## Workflow

1. Read `models/<model>/MODEL.md`.
2. Read the current benchmark evidence under `certifications/<model>/`.
3. Read the active OpenMC implementation under `models/<model>/openmc/model.py`.
4. Read any MCNP reference notes or reference deck analysis under
   `models/<model>/mcnp/`.
5. Read relevant study summaries under `studies/` that show how engineers have
   used the model.
6. Read material basis docs under `docs/references/materials/` when the model
   depends on generated materials such as `UO2F2`.
7. Draft or update `models/<model>/HANDOFF.md`.

## Benchmarking Section Rules

This section is the main trust-building section.

Do not just say that the model was "certified" or point at a checkpoint.
Summarize the actual comparison.

Include:

- what MCNP reference basis was used
- which cases were compared
- a table with `MCNP keff`, `OpenMC keff`, uncertainties, and `Delta keff`
- the maximum observed `Delta keff`
- any obvious systematic bias
- a short statement explaining why the benchmark was accepted for engineering
  use

If there is a remaining discrepancy, state it plainly.

## Configurable Parameters Section Rules

Make a clear distinction between:

- parameters engineers are expected to sweep
- baseline values used for benchmarking
- assumptions that are fixed in the template

Prefer a table with:

- parameter name
- meaning
- units
- baseline
- normal range
- notes

## Engineering Use Section Rules

This section explains how systems engineers have been using the model.

If there is not enough history yet, include a short placeholder that says the
model has primarily been used for early design-space exploration and list the
types of questions it is intended to answer.

Good examples:

- fill-height exploration
- H/U sensitivity checks
- spacing or separation studies
- moderator sensitivity checks
- bounding geometry studies

## Parameter Sensitivity / Lookup Sweeps Rules

Include simple one-parameter sweeps that act as lookup tables.

These are not the full study history. They are quick-reference sensitivity
tables that help reviewers and engineers understand how the model behaves when a
single parameter changes while the rest of the basis is held fixed.

Always include:

- the varied parameter
- the fixed baseline for all other key inputs
- the sweep table with `keff` and uncertainty
- a short interpretation of where max-keff or peak sensitivity occurs

Prioritize:

- `H/U` sweeps when relevant
- fill height
- separation distance
- enrichment
- moderator density

Use existing study reports when available instead of recomputing numbers.

## Material Definitions Rules

Describe both:

- shared library materials
- generated process materials

When generated materials are used, cite the actual basis documents and code
locations, for example:

- `critbuddy/core/materials/builders.py`
- `critbuddy/core/materials/material_specs.py`
- `critbuddy/core/materials/uo2f2_physics.py`
- `docs/references/materials/`

Do not paste long derivations into the handoff when a shorter summary plus file
references is sufficient.

## Guardrails

- Do not replace `MODEL.md` with the handoff doc.
- Do not describe the handoff as the final licensed MCNP deliverable.
- Do not hide OpenMC/MCNP discrepancies.
- Do not bury benchmark evidence in the appendix; keep it in the main body.
- Do not mix exploratory study outputs with frozen benchmark evidence without
  labeling them clearly.
- Prefer concise tables and short narrative over long prose.
