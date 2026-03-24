# Certification Format

## Directory Layout

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

## File Rules

- Keep the OpenMC sweep definition in `openmc/study.yaml`.
- Keep lightweight OpenMC outputs in `openmc/results/`.
- Keep only `input.inp` and `out` for MCNP case directories unless explicitly
  asked for more.
- Keep `results.md` as the only human summary inside the checkpoint.

## results.md Template

````md
# <Model> Certification <id>

This checkpoint preserves the OpenMC sweep config, lightweight OpenMC outputs,
and rerunnable MCNP case directories used for the solver-to-solver comparison.

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
