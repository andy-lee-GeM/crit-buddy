# Centrifuge Unit Cell Certification 2026-03-16-r1

This checkpoint preserves the OpenMC sweep config, lightweight OpenMC outputs,
and rerunnable MCNP case directories used for the canonical
`centrifuge-unit-cell` solver-to-solver comparison.

Run this certification from the git commit that contains this directory.

## Reproduce

OpenMC:

```bash
python run_study.py certifications/centrifuge-unit-cell/2026-03-16-r1/openmc/study.yaml
```

MCNP:

```bash
for case_dir in certifications/centrifuge-unit-cell/2026-03-16-r1/mcnp/fill_*; do
  (
    cd "$case_dir"
    mcnp6 i=input.inp o=out r=runtpe tasks 4
  )
done
```

## Results

| Case | MCNP keff | OpenMC keff | MCNP std | OpenMC std | Delta keff |
|------|-----------|-------------|----------|------------|------------|
| `fill_10` | 0.99269 | 0.99294 | 0.00096 | 0.00120 | +0.00025 |
| `fill_20` | 1.20945 | 1.21101 | 0.00093 | 0.00112 | +0.00156 |
| `fill_30` | 1.30067 | 1.30184 | 0.00084 | 0.00112 | +0.00117 |
| `fill_40` | 1.35134 | 1.35319 | 0.00095 | 0.00108 | +0.00185 |
| `fill_50` | 1.38045 | 1.38309 | 0.00089 | 0.00110 | +0.00264 |

Maximum absolute delta keff: `0.00264`.

Notes:
- `openmc/study.yaml` is the sweep definition.
- `openmc/results/` contains the copied OpenMC run outputs kept with this checkpoint.
- `fill_10` uses a manual MCNP source adjustment to keep the source inside the fuel region.
