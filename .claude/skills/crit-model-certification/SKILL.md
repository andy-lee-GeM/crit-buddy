---
name: crit-model-certification
description: Create or update lightweight model certification checkpoints under `certifications/`. Use when asked to freeze an OpenMC/MCNP parity checkpoint, preserve rerunnable MCNP cases plus lightweight OpenMC outputs, write `results.md`, or update the docs that point to the blessed certification.
---

# Skill: Crit Model Certification

Create a lightweight, rerunnable certification checkpoint. Preserve the OpenMC
sweep config, lightweight OpenMC outputs, the rerunnable MCNP case directories,
and a short `results.md` that lets a future engineer inspect and rerun the
comparison from git.

Read `references/format.md` when you need the exact directory tree, the
`results.md` template, or the repo documentation touch points.

## Workflow

1. Identify the source artifacts.
2. Create or update `certifications/<model>/<yyyy-mm-dd-rN>/`.
3. Copy the OpenMC sweep config into `openmc/study.yaml`.
4. Copy lightweight OpenMC outputs into `openmc/results/`.
5. Copy each MCNP case with only `input.inp` and `out`.
6. Write or refresh `results.md`.
7. Update the repo docs that point to the blessed checkpoint.

## Source Artifacts

Prefer copying from an existing parity study or from a manually assembled
checkpoint candidate. Treat copied run outputs as historical artifacts; do not
rewrite them unless explicitly asked to regenerate them.

Keep:

- `openmc/study.yaml`
- `openmc/results/results.csv`
- `openmc/results/REPORT.md`
- useful plots under `openmc/results/plots/`
- `mcnp/<case>/input.inp`
- `mcnp/<case>/out`
- `results.md`

Drop unless explicitly requested:

- `runtpe`
- `srctp`
- `xsdir`
- archived MCNP rerun outputs
- OpenMC statepoints and other heavy scratch

## results.md Requirements

Keep `results.md` short. It should:

- state what the certification preserves
- tell the reader to rerun from the git commit that contains the checkpoint
- include one OpenMC rerun command
- include one MCNP rerun loop or equivalent command
- include the solver comparison table
- note any important comparison caveats, such as manual source adjustments or
  shared-material MCNP decks

## Documentation Updates

When a checkpoint becomes the reference location, update:

- `README.md`
- `docs/model-certifications.md` if the format changed
- the relevant `models/<model>/MODEL.md`

## Guardrails

- Keep certifications under `certifications/`, not under `studies/`.
- Do not delete existing parity-study folders unless explicitly asked.
- Keep the certification self-contained enough to inspect and rerun later.
- Prefer a new `rN` directory over mutating an old checkpoint once it has been
  blessed.
