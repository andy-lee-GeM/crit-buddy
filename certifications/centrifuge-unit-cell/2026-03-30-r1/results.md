# Centrifuge Unit Cell Certification 2026-03-30-r1

This checkpoint preserves the OpenMC source snapshot, sweep config,
lightweight OpenMC outputs, and rerunnable MCNP case directories used for the
canonical `centrifuge-unit-cell` solver-to-solver comparison.

Run this certification from the git commit that contains this directory.

## Reproduce

OpenMC:

```bash
python run_study.py certifications/centrifuge-unit-cell/2026-03-30-r1/openmc/study.yaml --name cert-artifacts
```

MCNP:

```bash
for case_dir in certifications/centrifuge-unit-cell/2026-03-30-r1/mcnp/fill_*; do
  (
    cd "$case_dir"
    mcnp6 i=input.inp o=out r=runtpe tasks 4
  )
done
```

## Results

| Case | MCNP keff | OpenMC keff | MCNP std | OpenMC std | Delta keff |
|------|-----------|-------------|----------|------------|------------|
| `fill_10` | 0.99269 | 0.99000 | 0.00096 | 0.00103 | -0.00269 |
| `fill_20` | 1.20945 | 1.20785 | 0.00093 | 0.00104 | -0.00160 |
| `fill_30` | 1.30067 | 1.29851 | 0.00084 | 0.00106 | -0.00216 |
| `fill_40` | 1.35134 | 1.34520 | 0.00095 | 0.00111 | -0.00614 |
| `fill_50` | 1.38045 | 1.37936 | 0.00089 | 0.00105 | -0.00109 |

Maximum absolute delta keff: `0.00614`.

Notes:
- `openmc/model.py` is the frozen OpenMC source snapshot used to generate this
  checkpoint.
- `openmc/study.yaml` is the sweep definition.
- `openmc/cases/` contains the exported OpenMC model files for each case:
  `materials.xml`, `geometry.xml`, and `settings.xml`.
- `openmc/results/` contains the copied OpenMC run outputs kept with this checkpoint.
- `fill_10` uses a manual MCNP source adjustment to keep the source inside the fuel region.
- This checkpoint makes `enrichment_pct`, `h_to_u`, and `vessel_height_cm`
  explicit in `openmc/study.yaml` so the current OpenMC baseline is frozen
  instead of relying on model defaults.
- The certification now uses the shared `centrifuge_air` library material,
  which preserves the legacy MCNP air card while removing the prior humid-air
  regression from the OpenMC baseline.
- The remaining OpenMC/MCNP gap is small and uniformly negative across the fill
  sweep, with the worst case at `fill_40`.
