# ORNL/TM-12292 UO2F2 20% Sphere Benchmark

This study is the smallest OpenMC validation package for the `20 wt%`
`UO2F2-H2O` spherical benchmark basis from `ORNL/TM-12292`.

It exists to show two things:

1. The shared `H/X -> H/U -> density` path is traceable to the paper basis.
2. The shared `uo2f2-sphere-benchmark` model reproduces the same broad
   spherical moderation trend for the `20 wt%` case.

## Run

Geometry preview:

```bash
python run_study.py studies/ornl-tm-12292-uo2f2-20pct-sphere/configs/01_geometry_preview.yaml --validate
```

Validation sweep:

```bash
python run_study.py studies/ornl-tm-12292-uo2f2-20pct-sphere/configs/02_hx_validation_sweep.yaml
```

## Core Files

- `configs/01_geometry_preview.yaml`
- `configs/02_hx_validation_sweep.yaml`
- `reference/20pct_table_a3.csv`
- `reference/20pct_table_b1.csv`
- `reference/20pct_table_b2.csv`
- `results.md`

## Notes

- The benchmark model is `models/uo2f2-sphere-benchmark/`.
- The shared material implementation is
  `critbuddy/core/materials/uo2f2_physics.py`.
- Standard run artifacts under `_validation/` and `runs/` are generated output,
  not part of the core study definition.
