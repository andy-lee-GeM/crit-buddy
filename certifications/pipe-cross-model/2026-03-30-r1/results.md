# Pipe Cross Model Certification 2026-03-30-r1

This checkpoint preserves the OpenMC source snapshot, sweep config,
lightweight OpenMC outputs, and rerunnable MCNP case directories used for the
`pipe-cross-model` solver-to-solver comparison.

Run this certification from the git commit that contains this directory.

## Reproduce

OpenMC:

```bash
python run_study.py certifications/pipe-cross-model/2026-03-30-r1/openmc/study.yaml --name cert-artifacts
```

MCNP:

```bash
for case_dir in certifications/pipe-cross-model/2026-03-30-r1/mcnp/sep_*; do
  (
    cd "$case_dir"
    mcnp6 i=input.inp o=out r=runtpe tasks 4
  )
done
```

## Results

| Case | MCNP keff | OpenMC keff | MCNP std | OpenMC std | Delta keff |
|------|-----------|-------------|----------|------------|------------|
| `sep_0.0` | 1.09818 | 1.10710 | 0.00080 | 0.00116 | +0.00892 |
| `sep_5.8` | 0.97525 | 0.98513 | 0.00085 | 0.00124 | +0.00988 |
| `sep_6.5` | 0.95600 | 0.96435 | 0.00078 | 0.00117 | +0.00835 |
| `sep_7.0` | 0.94355 | 0.95080 | 0.00081 | 0.00111 | +0.00725 |

Maximum absolute delta keff: `0.00988`.

Notes:
- `openmc/model.py` is the frozen OpenMC source snapshot used to generate this
  checkpoint.
- `openmc/study.yaml` is the sweep definition.
- `openmc/cases/` contains the exported OpenMC model files for each case:
  `materials.xml`, `geometry.xml`, and `settings.xml`.
- `openmc/results/` contains the copied OpenMC run outputs kept with this checkpoint.
- The MCNP cases in this certification use OpenMC builder materials for the parity comparison.
- This rerun reproduced the prior 2026-03-24 checkpoint values to the same reported precision.
