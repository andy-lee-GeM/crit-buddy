---
name: create-model-handoff
description: Create or update the full consultant-facing handoff workflow for a crit-buddy canonical model. Use when asked to author or refresh `models/<model>/HANDOFF.md`, generate the reviewer-facing handoff package in markdown and docx, copy supporting artifacts into the curated handoff bundle, include reviewer-facing visualizations and selected case inputs, export material library cards, and place the runnable OpenMC and MCNP reference models in `models/model.py` and `models/model.inp`.
---

# Skill: Create Model Handoff

Create the full reviewer-facing handoff deliverable for a canonical crit-buddy
model.

This skill now owns both:

- authoring or updating the canonical handoff document at
  `models/<model>/HANDOFF.md`
- generating the curated handoff package under `handoffs/<model>/`

This skill produces a local handoff package under:

- `handoffs/<model>/`

Inside that package:

- the curated reviewer-facing files live at the top level
- the minimal certification-style backing artifacts live under `data/`

Read `references/directory-structure.md` for the expected output layout.
Read `references/report-sections.md` for the report section order and content.

## Handoff Document Ownership

Treat `models/<model>/HANDOFF.md` as the canonical authored source for the
reviewer narrative.

The generated package should copy from that canonical document after it has been
authored or refreshed. Do not maintain separate independent narratives in
`models/<model>/HANDOFF.md` and `handoffs/<model>/report/handoff.md`.

If the user asks only for the document and not the package, stop after updating
`models/<model>/HANDOFF.md` unless they ask for packaging too.

## Handoff Document Goals

The canonical handoff document should help a reviewer understand:

- what physical system the model represents
- what parameters engineers can change
- what assumptions are fixed in the template
- what materials are used and where they come from
- how the model is run in OpenMC
- how OpenMC was benchmarked against MCNP
- how engineers have used the model so far
- how sensitive `k-effective` is to major one-parameter sweeps
- where the model should and should not be used

## Required Document Sections

Use the section order from `references/report-sections.md` unless the user asks
for something narrower:

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

## Core Requirements

The local handoff package should contain:

- `report/handoff.md`
- `report/handoff.docx`
- `models/model.py`
- `models/model.inp`
- `materials/material-library.md`
- `materials/mcnp-material-cards.txt`
- selected `figures/`
- selected `artifacts/`
- `data/`

The `models/` directory in the report repo is intentionally small.

It should contain only:

- the canonical OpenMC `model.py`
- the reference MCNP input deck copied as `model.inp`

If the source MCNP file is named something else such as `reference.inp`, copy it
into the report repo as `models/model.inp`.

## Source Inputs

Gather material from the canonical model and its supporting evidence:

- `models/<model>/MODEL.md`
- `models/<model>/HANDOFF.md` if it already exists
- `models/<model>/openmc/model.py`
- `models/<model>/mcnp/`
- `certifications/<model>/`
- relevant `studies/`
- material basis docs under `docs/references/materials/`

## Workflow

1. Identify the canonical model and the intended handoff revision.
2. Identify the frozen benchmark checkpoint to cite in the report.
3. Identify the study artifacts to include as lookup sweeps or engineering-use
   evidence.
4. Build or update the canonical handoff markdown report at
   `models/<model>/HANDOFF.md`.
5. Generate `report/handoff.docx` from the packaged markdown report using the
   repo's docx generator.
6. Copy the runnable reference model files into:
   - `models/model.py`
   - `models/model.inp`
7. Export the material library summary and MCNP-ready material cards.
8. Copy selected visualizations into `figures/`.
9. Copy selected benchmark and sweep artifacts into `artifacts/`.
10. Copy the minimal supporting artifact set into `data/`.
11. Create or update the local handoff package under `handoffs/<model>/`.

## Document Authoring Rules

### Benchmarking Section

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

### Configurable Parameters Section

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

### Engineering Use Section

Explain how systems engineers have been using the model.

If there is not enough history yet, include a short placeholder that says the
model has primarily been used for early design-space exploration and list the
types of questions it is intended to answer.

Good examples:

- fill-height exploration
- H/U sensitivity checks
- spacing or separation studies
- moderator sensitivity checks
- bounding geometry studies

### Parameter Sensitivity / Lookup Sweeps

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

### Material Definitions

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

## Local Package Rules

The generated package under `handoffs/<model>/` is the curated reviewer bundle
plus its local backing data.

Keep it clean and intentional.

Include:

- the polished report in markdown and docx
- the exact OpenMC `model.py`
- the exact MCNP reference deck as `model.inp`
- only the most relevant figures
- only the most useful summary artifacts
- material-library documentation
- MCNP-ready material cards

Do not dump the full raw study tree into the top-level curated directories.
Keep `data/` in a certification-style minimal form.

## Data Rules

The `data/` subtree is the minimal copied backing store for artifacts.

Use it for:

- benchmark `openmc/model.py`
- benchmark `openmc/study.yaml`
- benchmark `openmc/cases/`
- benchmark `openmc/results/`
- benchmark rerunnable MCNP case directories containing `input.inp` and `out`
- benchmark `results.md`
- minimal sweep files such as `study.yaml`, `report.md`, and `results.csv`

The `data/` subtree should preserve useful evidence, but stay close to the
lightweight certification style instead of copying every generated run artifact.

## Report Generation Rules

Write the narrative report first as `models/<model>/HANDOFF.md`.

Then generate the docx with the existing repo tooling:

- `critbuddy/reporting/docx_generator.py`

The packaged `report/handoff.md` should be copied from the canonical
`models/<model>/HANDOFF.md` after that document has been updated.

Prefer reusing existing markdown handoff content when available rather than
rewriting the report from scratch.

## Material Export Rules

Use the existing material tooling when possible:

- `scripts/list_mcnp_materials.py`
- `critbuddy/core/materials/`
- `docs/references/materials/`

The report package should include:

- a concise material-library summary
- MCNP-ready material cards needed to inspect or reproduce the basis materials

## Visualizations

Include only figures that materially help a reviewer:

- benchmark trend plots
- one-parameter sensitivity plots
- geometry visualizations when available

Do not include large numbers of low-signal plots.

## Selected Artifacts

Good candidates for the top-level curated package:

- benchmark `results.md`
- benchmark `study.yaml`
- selected sweep `report.md`
- selected sweep `study.yaml`

The copied case exports and selected raw outputs belong in `data/`, but keep
that subtree intentionally minimal.

## Guardrails

- Do not replace `models/<model>/MODEL.md` inside the source repo.
- Do not maintain conflicting narratives between `models/<model>/HANDOFF.md`
  and the packaged `report/handoff.md`.
- Do not treat the handoff package as the final licensed MCNP deliverable.
- Do not omit known OpenMC / MCNP discrepancies from the report.
- Do not leave the package without the actual `model.py` and `model.inp`.
- Do not put extra source files in the package `models/` directory.
- Do not depend on link-only references when copying the real files is feasible.
