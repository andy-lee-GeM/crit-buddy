# Model Certifications

Model certifications are lightweight, frozen checkpoints kept under
`certifications/`. They are not exploratory studies. Their job is to preserve
enough input and output material to inspect the comparison later and rerun it
from the same git commit.

## Layout

```text
certifications/<model>/<yyyy-mm-dd-rN>/
  openmc/
    study.yaml
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

## Contents

- Keep the OpenMC sweep config in `openmc/study.yaml`.
- Keep lightweight OpenMC outputs in `openmc/results/`.
- Keep only rerunnable MCNP case artifacts: `input.inp` and `out`.
- Keep a short `results.md` with reproduction commands and the comparison table.
- Do not keep heavy scratch artifacts such as `runtpe`, `srctp`, `xsdir`, or
  OpenMC statepoints unless there is a specific reason to bless them.

## Workflow

1. Create a new checkpoint directory under `certifications/<model>/<id>/`.
2. Copy the OpenMC sweep config and the lightweight OpenMC output files.
3. Copy each MCNP case directory with only `input.inp` and `out`.
4. Write `results.md` with rerun commands and a solver comparison table.
5. Update the model documentation when the checkpoint becomes the current
   reference certification.

Existing examples:

- `certifications/centrifuge-unit-cell/2026-03-16-r1/`
- `certifications/pipe-cross-model/2026-03-24-r1/`

For future Codex sessions, use `$crit-model-certification` to create or update
this structure.
