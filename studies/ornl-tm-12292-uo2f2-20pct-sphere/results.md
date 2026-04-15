# ORNL/TM-12292 20% Sphere Comparison

This study compares a small fixed-radius OpenMC sweep against the `20 wt%`
ORNL spherical benchmark trend.

The comparison is intentionally limited to one claim:

- if we hold the sphere geometry fixed and sweep the paper's `H/X` points,
  does the OpenMC `k-eff` curve peak in the same moderation region indicated by
  the ORNL spherical tables?

This study does not try to reproduce the entire ORNL critical-radius search.

## Basis

- Model: `uo2f2-sphere-benchmark`
- Config: `configs/02_hx_validation_sweep.yaml`
- Enrichment: `20.00 wt% U-235`
- Fuel sphere radius: `13.88 cm`
- Reflector: `100 cm` water shell at `1.0 g/cm3`
- Outer boundary: `vacuum`
- Run results: `runs/02_hx_validation_sweep/latest/results.csv`

The `13.88 cm` radius is taken directly from ORNL Table B.2 for the `20 wt%`,
`H/X = 100` critical sphere. That gives one paper-anchored spherical geometry
to use for the fixed-radius sweep.

## What The ORNL Tables Say

For the `20 wt%` case:

- Table B.1 `k4` peaks at `H/X = 100` with `k4 = 1.67708`
- Table B.1 is nearly flat from `H/X = 100` to `200`
- Table B.2 minimum critical volume is at `H/X = 100`
- Table B.2 minimum uranium mass is at `H/X = 500`

That last point matters. `H/X = 500` is the minimum-mass point, not the peak
reactivity point. For a fixed-radius sphere, the expected peak should be near
the ORNL reactivity and minimum-volume region, around `H/X = 100-200`.

## OpenMC Result

The OpenMC fixed-radius sweep peaks at:

- `H/X = 100`
- exact `H/U = 20.204171`
- `k-eff = 0.99369 +/- 0.00113`

The next point, `H/X = 200`, is slightly lower at `k-eff = 0.98330`. The curve
then falls off at higher moderation:

- `H/X = 300` -> `0.94631`
- `H/X = 500` -> `0.87221`
- `H/X = 700` -> `0.80408`

That is the same broad trend region as ORNL Table B.1 and Table B.2 for the
most reactive spherical behavior.

## Apples-To-Apples Trend Check

| H/X | Exact H/U | ORNL Table B.1 k4 | OpenMC k-eff |
| ---: | ---: | ---: | ---: |
| 0.0 | 0.000000 | 1.37262 | 0.61130 |
| 5.0 | 1.010209 | 1.40257 | 0.71424 |
| 10.0 | 2.020417 | 1.43940 | 0.80386 |
| 20.0 | 4.040834 | 1.50977 | 0.87303 |
| 50.0 | 10.102086 | 1.62091 | 0.95927 |
| 100.0 | 20.204171 | 1.67708 | 0.99369 |
| 200.0 | 40.408342 | 1.67553 | 0.98330 |
| 300.0 | 60.612514 | 1.63703 | 0.94631 |
| 500.0 | 101.020856 | 1.53996 | 0.87221 |
| 700.0 | 141.429198 | 1.44376 | 0.80408 |

The absolute values are different because `k4` and `k-eff` are different
quantities. The useful comparison is the trend location:

- ORNL peak reactivity region: `H/X = 100-200`
- OpenMC fixed-radius peak region: `H/X = 100-200`
- ORNL minimum uranium mass point: `H/X = 500`
- OpenMC fixed-radius peak is not at `500`, which is expected

## OpenMC Sweep Table

| H/X | Exact H/U | UO2F2 density (g/cm3) | k-eff | std |
| ---: | ---: | ---: | ---: | ---: |
| 0.0 | 0.000000 | 6.42213 | 0.61130 | 0.00092 |
| 5.0 | 1.010209 | 6.18127 | 0.71424 | 0.00101 |
| 10.0 | 2.020417 | 5.91562 | 0.80386 | 0.00111 |
| 20.0 | 4.040834 | 4.73280 | 0.87303 | 0.00108 |
| 50.0 | 10.102086 | 3.12803 | 0.95927 | 0.00118 |
| 100.0 | 20.204171 | 2.23909 | 0.99369 | 0.00113 |
| 200.0 | 40.408342 | 1.67435 | 0.98330 | 0.00111 |
| 300.0 | 60.612514 | 1.46277 | 0.94631 | 0.00116 |
| 500.0 | 101.020856 | 1.28382 | 0.87221 | 0.00110 |
| 700.0 | 141.429198 | 1.20431 | 0.80408 | 0.00097 |

## OpenMC vs MCNP Comparison

The same `H/X` sweep was rerun through the model's MCNP path using the shared
`UO2F2` density / `H/X -> H/U` conversion basis and study-owned case outputs:

- OpenMC results: `runs/02_hx_validation_sweep/latest/results.csv`
- MCNP results: `runs/02_hx_validation_sweep_mcnp/latest/results.csv`
- MCNP case outputs: `runs/02_hx_validation_sweep_mcnp/latest/cases/`

The solver-to-solver comparison shows the same broad moderation shape and the
same preferred region near `H/X = 100-200`, with MCNP lower than OpenMC at all
sampled points.

| H/X | OpenMC k-eff | MCNP k-eff | OpenMC std | MCNP std | Delta (MCNP - OpenMC) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0 | 0.61130 | 0.61043 | 0.00092 | 0.00076 | -0.00087 |
| 5.0 | 0.71424 | 0.71196 | 0.00101 | 0.00074 | -0.00228 |
| 10.0 | 0.80386 | 0.79872 | 0.00111 | 0.00095 | -0.00514 |
| 20.0 | 0.87303 | 0.86960 | 0.00108 | 0.00094 | -0.00343 |
| 50.0 | 0.95927 | 0.95573 | 0.00118 | 0.00092 | -0.00354 |
| 100.0 | 0.99369 | 0.98888 | 0.00113 | 0.00097 | -0.00481 |
| 200.0 | 0.98330 | 0.97921 | 0.00111 | 0.00080 | -0.00409 |
| 300.0 | 0.94631 | 0.94557 | 0.00116 | 0.00096 | -0.00074 |
| 500.0 | 0.87221 | 0.87124 | 0.00110 | 0.00086 | -0.00097 |
| 700.0 | 0.80408 | 0.80284 | 0.00097 | 0.00073 | -0.00124 |

For this study basis:

- both solvers peak in the same `H/X = 100-200` region
- both solvers classify `H/X = 50`, `100`, and `200` as `MARGINAL`
- MCNP is lower at every point by about `271 pcm` on average
- the largest sampled gap is about `514 pcm` at `H/X = 10`

## Infinite Reflection Check

On April 10, 2026, the same fixed-radius `H/X` sweep was rerun with:

- Config: `configs/03_hx_infinite_reflection_sweep.yaml`
- Outer boundary: `reflective`
- Run results: `runs/03_hx_infinite_reflection_sweep/latest/results.csv`

The reflective rerun produced the same sampled `k-eff` and `std` values at
every `H/X` point as the original `vacuum`-boundary run. The only material
difference in the result CSV is the recorded `outer_boundary_type` value.

That means the `100 cm` light-water shell is already thick enough that changing
the outer spherical boundary from `vacuum` to `reflective` did not move the
observed moderation trend for this study basis.

| H/X | Vacuum k-eff | Reflective k-eff | Delta |
| ---: | ---: | ---: | ---: |
| 0.0 | 0.61130 | 0.61130 | 0.00000 |
| 5.0 | 0.71424 | 0.71424 | 0.00000 |
| 10.0 | 0.80386 | 0.80386 | 0.00000 |
| 20.0 | 0.87303 | 0.87303 | 0.00000 |
| 50.0 | 0.95927 | 0.95927 | 0.00000 |
| 100.0 | 0.99369 | 0.99369 | 0.00000 |
| 200.0 | 0.98330 | 0.98330 | 0.00000 |
| 300.0 | 0.94631 | 0.94631 | 0.00000 |
| 500.0 | 0.87221 | 0.87221 | 0.00000 |
| 700.0 | 0.80408 | 0.80408 | 0.00000 |

## Conclusion

This study supports the narrow validation claim we wanted:

- the paper-facing `H/X` inputs map to the expected exact `H/U` values
- the OpenMC sphere model shows the same broad spherical moderation trend as
  the ORNL `20 wt%` benchmark
- the most reactive fixed-radius region is around `H/X = 100-200`
- `H/X = 500` should be interpreted as the minimum critical uranium mass point,
  not the fixed-radius peak-reactivity point
- the MCNP rerun of the same ten study points shows the same moderation-shape
  conclusion as OpenMC, while landing modestly lower in absolute `k-eff`
- rerunning the same sweep with an explicitly `reflective` outer boundary did
  not change the sampled results for this `100 cm` water-reflected basis

## Artifacts

- Geometry preview: `_validation/geometry.png`
- Standard results: `runs/02_hx_validation_sweep/latest/results.csv`
- `k-eff` vs `H/X`: `runs/02_hx_validation_sweep/latest/plots/keff_vs_h_over_x.png`
- `k-eff` vs exact `H/U`: `runs/02_hx_validation_sweep/latest/plots/keff_vs_h_to_u.png`
- MCNP results: `runs/02_hx_validation_sweep_mcnp/latest/results.csv`
- MCNP case outputs: `runs/02_hx_validation_sweep_mcnp/latest/cases/`
- Infinite-reflection results: `runs/03_hx_infinite_reflection_sweep/latest/results.csv`
- Infinite-reflection `k-eff` vs `H/X`: `runs/03_hx_infinite_reflection_sweep/latest/plots/keff_vs_h_over_x.png`
- Infinite-reflection `k-eff` vs exact `H/U`: `runs/03_hx_infinite_reflection_sweep/latest/plots/keff_vs_h_to_u.png`
