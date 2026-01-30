# ORNL 30B Benchmark Comparison

Comparison of Crit-Buddy OpenMC results against ORNL/TM-2021/2043 reference values for single 30B UF6 cylinders with water reflection.

## Reference: ORNL/TM-2021/2043 Table 2

k-eff values for single 30B cylinders with infinite water reflection (KENO-VI/SCALE):

| Enrichment (wt%) | 2.5 g/cc | 3.5 g/cc | 4.5 g/cc | 5.5 g/cc |
|------------------|----------|----------|----------|----------|
| 6                | 0.5049   | 0.5600   | 0.6053   | 0.6401   |
| 7                | 0.5274   | 0.5889   | 0.6393   | 0.6801   |
| 8                | 0.5458   | 0.6143   | 0.6704   | 0.7166   |
| 9                | 0.5651   | 0.6380   | 0.6992   | 0.7489   |
| 10               | 0.5825   | 0.6611   | 0.7262   | 0.7798   |
| 12               | 0.6129   | 0.7016   | 0.7763   | 0.8366   |
| 15               | 0.6533   | 0.7561   | 0.8422   | 0.9091   |
| 20               | 0.7127   | 0.8354   | 0.9348   | 1.0119   |

## Crit-Buddy OpenMC Results

k-eff values from `runs/ornl_b1/2026-01-29_18-22-40/results.csv`:

| Enrichment (wt%) | 2.5 g/cc | 3.5 g/cc | 4.5 g/cc | 5.5 g/cc |
|------------------|----------|----------|----------|----------|
| 6                | 0.5096   | 0.5634   | 0.6087   | 0.6451   |
| 7                | 0.5313   | 0.5918   | 0.6433   | 0.6856   |
| 8                | 0.5503   | 0.6172   | 0.6744   | 0.7213   |
| 9                | 0.5688   | 0.6411   | 0.7044   | 0.7550   |
| 10               | 0.5862   | 0.6646   | 0.7324   | 0.7845   |
| 12               | 0.6152   | 0.7056   | 0.7804   | 0.8409   |
| 15               | 0.6568   | 0.7598   | 0.8471   | 0.9140   |
| 20               | 0.7150   | 0.8389   | 0.9385   | 1.0165   |

## Summary

The OpenMC results show good agreement with the ORNL KENO-VI reference calculations. Differences are typically within 0.5% dk, which is consistent with expected variations between Monte Carlo codes using different cross-section libraries and geometric discretization approaches. Both codes correctly predict the 20 wt% / 5.5 g/cc case as supercritical (k-eff > 1.0).
