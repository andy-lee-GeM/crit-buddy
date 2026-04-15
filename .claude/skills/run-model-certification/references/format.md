# Certification Format

## Directory Layout

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

## File Rules

- Keep the OpenMC source snapshot in `openmc/model.py` so the checkpoint
  records the exact source used to create the frozen artifacts.
- Keep the OpenMC sweep definition in `openmc/study.yaml`.
- Keep deterministic per-case OpenMC exports in `openmc/cases/`.
- Keep lightweight OpenMC outputs in `openmc/results/`.
- Keep only `input.inp` and `out` for MCNP case directories unless explicitly
  asked for more.
- Keep `results.md` as the only human summary inside the checkpoint.
- Do not keep heavy scratch artifacts such as `runtpe`, `srctp`, `xsdir`, or
  regenerated OpenMC statepoints unless there is a specific reason to bless
  them.

## Workflow

1. Create a new checkpoint directory under `certifications/<model>/<id>/`.
2. Copy the OpenMC `model.py` source snapshot.
3. Copy the OpenMC sweep config and lightweight OpenMC output files.
4. Copy each MCNP case directory with only `input.inp` and `out`.
5. Write `results.md` with rerun commands and a solver comparison table.
6. Update the model documentation when the checkpoint becomes the current
   reference certification.

Existing examples:

- `certifications/centrifuge-unit-cell/2026-03-30-r1/`
- `certifications/pipe-cross-model/2026-03-30-r1/`

## results.md Template

````md
# <Model> Certification <id>

This checkpoint preserves the OpenMC source snapshot, sweep config, lightweight
OpenMC outputs, and rerunnable MCNP case directories used for the
solver-to-solver comparison.

Run this certification from the git commit that contains this directory.

## Reproduce

```bash
python run_study.py certifications/<model>/<id>/openmc/study.yaml
```

```bash
for case_dir in certifications/<model>/<id>/mcnp/*; do
  (
    cd "$case_dir"
    mcnp6 i=input.inp o=out r=runtpe tasks 4
  )
done
```

## Results

| Case | MCNP keff | OpenMC keff | MCNP std | OpenMC std | Delta keff |
|------|-----------|-------------|----------|------------|------------|
| ...  | ...       | ...         | ...      | ...        | ...        |
````

## Documentation Touch Points

- `README.md`
- `docs/model-certifications.md`
- `models/<model>/MODEL.md`
