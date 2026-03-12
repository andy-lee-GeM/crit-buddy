# Steven Film Review

This experiment folder packages the OpenMC recreation of the Steven thin-film
case from [mcnp-steven-film.inp](/home/gem/Projects/crit-buddy/reports/steven-film-review/source/mcnp-steven-film.inp).

## Purpose

Provide a self-contained place to compare the reference MCNP model against the
OpenMC reconstruction for the approximately 20 wt% enriched fissile film case.

## Layout

- [_config/01_export_openmc.sh](/home/gem/Projects/crit-buddy/reports/steven-film-review/_config/01_export_openmc.sh)
  exports the OpenMC XML model using the repo script.
- [source/mcnp-steven-film.inp](/home/gem/Projects/crit-buddy/reports/steven-film-review/source/mcnp-steven-film.inp)
  is the reference MCNP input used for reconstruction.
- [runs/steven_film_openmc](/home/gem/Projects/crit-buddy/reports/steven-film-review/runs/steven_film_openmc)
  contains the exported `materials.xml`, `geometry.xml`, `settings.xml`, and `plots.xml`.

## Model Basis

The OpenMC model is built by [scripts/steven_film_openmc.py](/home/gem/Projects/crit-buddy/scripts/steven_film_openmc.py).

Current assumptions carried into the OpenMC recreation:

- periodic boundary conditions in `x/y` to represent the infinite lattice
- vacuum boundary conditions in `z`
- fuel occupies `10.0 <= z < 11.70 cm`
- bottom water occupies `0.0 <= z < 1.0 cm`
- top water occupies `99.0 <= z < 100.0 cm`
- internal air fills the remaining vessel free volume
- fuel material reproduces the MCNP `m1` atom ratios directly

## Regenerate The XML

```bash
bash reports/steven-film-review/_config/01_export_openmc.sh
```

## Run OpenMC

From the exported run directory:

```bash
cd reports/steven-film-review/runs/steven_film_openmc
openmc
```
