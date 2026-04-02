# Directory Structure

Use one local output package per model:

- `handoffs/<model>/`

Inside that package, keep the curated report files at the top level and the
minimal certification-style supporting artifacts under `data/`.

## Local Package

```text
 handoffs/<model>/
  README.md
  report/
    handoff.md
    handoff.docx
  models/
    model.py
    model.inp
  materials/
    material-library.md
    mcnp-material-cards.txt
  figures/
    benchmark/
    sensitivities/
    geometry/
  artifacts/
    benchmark/
      results.md
      study.yaml
    sensitivities/
      <sweep-name>-report.md
      <sweep-name>-study.yaml
  data/
    benchmark/
      openmc/
        model.py
        study.yaml
        cases/
        results/
      mcnp/
        <case>/
          input.inp
          out
      results.md
    sensitivities/
      <sweep-name>/
        study.yaml
        report.md
        results.csv
```

Rules:

- `models/` must contain only `model.py` and `model.inp`
- rename the copied MCNP reference deck to `model.inp`
- keep the top-level package curated
- keep `data/` close to the lightweight certification structure
