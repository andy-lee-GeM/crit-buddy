# Criticality Model Handoff Template

The canonical handoff authoring instructions now live in:

- `.claude/skills/create-model-handoff/SKILL.md`
- `.claude/skills/create-model-handoff/references/report-sections.md`
- `.claude/skills/create-model-handoff/references/report-template.md`
- `.claude/skills/create-model-handoff/references/directory-structure.md`

Use that skill when authoring or refreshing `models/<model>/HANDOFF.md` or when
building a curated handoff package under `handoffs/<model>/`.

## Repo-facing Summary

The canonical authored narrative belongs in:

- `models/<model>/HANDOFF.md`

The generated package belongs in:

- `handoffs/<model>/`

It should help a reviewer understand:

- what physical system the model represents
- what parameters engineers can change
- what assumptions are fixed
- what materials and solver setup were used
- how OpenMC was benchmarked against MCNP
- how engineers have used the model
- where the model should and should not be used
