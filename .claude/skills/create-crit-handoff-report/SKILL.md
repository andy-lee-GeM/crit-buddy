---
name: create-crit-handoff-report
description: Generate a consultant-facing criticality model handoff package from a crit-buddy canonical model. Use when asked to create a new handoff repo, write the report in markdown and docx, copy supporting artifacts into a separate data repo, include reviewer-facing visualizations and selected case inputs, export material library cards, and place the runnable OpenMC and MCNP reference models in `models/model.py` and `models/model.inp`.
---

# Skill: Create Crit Handoff Report

Create a reviewer-facing handoff package for a canonical crit-buddy model.

This skill produces a local handoff package under:

- `models/handoffs/<model>/`

Inside that package:

- the curated reviewer-facing files live at the top level
- the minimal certification-style backing artifacts live under `data/`

Read `references/directory-structure.md` for the expected output layout.
Read `references/report-sections.md` for the report section order and content.

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
4. Build or update the handoff markdown report.
5. Generate `report/handoff.docx` from the markdown report using the repo's
   docx generator.
6. Copy the runnable reference model files into:
   - `models/model.py`
   - `models/model.inp`
7. Export the material library summary and MCNP-ready material cards.
8. Copy selected visualizations into `figures/`.
9. Copy selected benchmark and sweep artifacts into `artifacts/`.
10. Copy the minimal supporting artifact set into `data/`.
11. Create or update the local handoff package under `models/handoffs/<model>/`.

## Local Package Rules

The generated package under `models/handoffs/<model>/` is the curated reviewer
bundle plus its local backing data.

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

Write the narrative report first as markdown.

Then generate the docx with the existing repo tooling:

- `critbuddy/reporting/docx_generator.py`

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
- Do not treat the handoff package as the final licensed MCNP deliverable.
- Do not omit known OpenMC / MCNP discrepancies from the report.
- Do not leave the package without the actual `model.py` and `model.inp`.
- Do not put extra source files in the package `models/` directory.
- Do not depend on link-only references when copying the real files is feasible.
