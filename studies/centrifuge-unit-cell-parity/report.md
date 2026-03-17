# Centrifuge Unit Cell OpenMC/MCNP Comparison

## Objective

Compare the canonical `centrifuge-unit-cell` OpenMC model against manual MCNP
case files built from the same reflective unit-cell geometry for fill heights
from 10 cm through 50 cm.

## Structure

| Path | Purpose |
|------|---------|
| `study.yaml` | OpenMC sweep definition |
| `openmc/runs/` | Raw OpenMC run outputs |
| `mcnp/fill_*/` | Manual MCNP case directories and outputs |
| `results.csv` | Combined solver results with a `solver` column |
| `report.md` | Human-readable comparison summary |

## Sweep Matrix

| Case | Fill plane | Fill fraction | MCNP source z | Notes |
|------|------------|---------------|---------------|-------|
| `fill_10` | `surface 9 = pz 10` | `0.1` | `5` | Keeps source inside the fuel region |
| `fill_20` | `surface 9 = pz 20` | `0.2` | `10` | Matches the canonical deck |
| `fill_30` | `surface 9 = pz 30` | `0.3` | `10` | Literal deck copy plus fill change |
| `fill_40` | `surface 9 = pz 40` | `0.4` | `10` | Literal deck copy plus fill change |
| `fill_50` | `surface 9 = pz 50` | `0.5` | `10` | Literal deck copy plus fill change |

## Comparison Summary

| Fill z (cm) | MCNP keff | OpenMC keff | MCNP std | OpenMC std | Delta keff |
|-------------|-----------|-------------|----------|------------|------------|
| 10 | 0.99269 | 0.99294 | 0.00096 | 0.00120 | +0.00025 |
| 20 | 1.20945 | 1.21101 | 0.00093 | 0.00112 | +0.00156 |
| 30 | 1.30067 | 1.30184 | 0.00084 | 0.00112 | +0.00117 |
| 40 | 1.35134 | 1.35319 | 0.00095 | 0.00108 | +0.00185 |
| 50 | 1.38045 | 1.38309 | 0.00089 | 0.00110 | +0.00264 |

## Conclusion

Completed cases: 5/5. Maximum absolute delta keff = 0.00264.
