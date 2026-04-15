# Model Certifications

Model certifications are lightweight, frozen checkpoints kept under
`certifications/`. They are not exploratory studies. Their job is to preserve
enough input and output material to inspect the comparison later and rerun it
from the same git commit.

The canonical operator workflow now lives in:

- `.claude/skills/run-model-certification/SKILL.md`
- `.claude/skills/run-model-certification/references/format.md`

Use that skill when creating or refreshing a checkpoint.

## Repo-facing Summary

The checkpoint layout is:

```text
certifications/<model>/<yyyy-mm-dd-rN>/
  openmc/
    model.py
    study.yaml
    cases/
      <case>/
        materials.xml
        geometry.xml
        settings.xml
    results/
      results.csv
      REPORT.md
      plots/
  mcnp/
    <case>/
      input.inp
      out
  results.md
```

Keep:

- the OpenMC source snapshot
- the sweep config
- deterministic per-case OpenMC exports
- lightweight OpenMC results
- rerunnable MCNP `input.inp` and `out`
- a short `results.md`

Existing examples:

- `certifications/centrifuge-unit-cell/2026-03-30-r1/`
- `certifications/pipe-cross-model/2026-03-30-r1/`
