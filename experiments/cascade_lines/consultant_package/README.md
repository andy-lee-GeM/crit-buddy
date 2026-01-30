# Consultant Verification Package

## Experiment: Cascade Lines Criticality Analysis

This package contains all information needed to independently verify
the criticality calculations performed for this experiment.

## Contents

| File | Description |
|------|-------------|
| specification.md | Complete methodology, assumptions, and parameters |
| materials.yaml | Exact isotopic compositions used in calculations |
| results.csv | Calculated k-eff values for all cases |
| geometry.png | Geometry visualization |
| example_inputs/ | Example input files (OpenMC/MCNP) |

## Verification Steps

1. Review **specification.md** to understand the analysis methodology
2. Verify **materials.yaml** matches your material definitions exactly
3. Build your model using the geometry and materials specified
4. Compare your input files to **example_inputs/** for syntax verification
5. Run calculations and compare to **results.csv**
6. Results should match within statistical uncertainty (k-eff ± 2σ)

## Acceptance Criteria

k-eff + 2σ < 0.95 (per ANSI/ANS-8.1)

## Nuclear Data

- Library: ENDF/B-VIII.0
- Temperature: 293 K (room temperature)

## Questions

Contact: [Your contact information here]
