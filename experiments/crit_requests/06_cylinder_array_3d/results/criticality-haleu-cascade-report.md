# Criticality Safety Evaluation: Cascade Cylinder Array

## Safe-by-Design Demonstration

| Document Information | |
|---------------------|---|
| **Document Number** | CSE-2026-001 |
| **Revision** | 0 |
| **Date** | 2026-02-13 |
| **Status** | DRAFT - FOR REVIEW |

| Prepared By | Reviewed By | Approved By |
|-------------|-------------|-------------|
| | | |
| Date: | Date: | Date: |

---

## Executive Summary

**Finding: The cascade cylinder array is safe by design. Criticality is not credible given operating conditions and equipment design.**

### Why UO2F2 Cannot Cause Criticality

| | Critical Threshold | Max Accumulation | Margin |
|---|-------------------|------------------|--------|
| **Fill fraction** | 2.5% | 0.29% | **8.6×** |
| **Mass per cylinder** | 2.5 kg | 283 g | **8.8×** |

- The critical threshold (2.5% fill) represents the **minimum** amount of material needed for criticality
- Maximum accumulation (0.29% fill) assumes **worst case**: 100% humidity, 100% water deposition, 100% reaction to UO2F2 at peak moderation (H/U=25), over entire 10-year equipment lifetime
- Even under these extreme assumptions, accumulation reaches only **1/9th** of the critical threshold

### Why UF6 Cannot Cause Criticality

| | Critical Threshold | Operating Limit | Margin |
|---|-------------------|-----------------|--------|
| **Mass per cylinder** | 5.2 kg | 5 g | **1,040×** |

- The critical threshold (5.2 kg solid UF6) is **1,000× higher** than the operating limit (5 g)
- UF6 would need to solidify and continuously accumulate to reach criticality — this is not credible given process conditions

### Conclusion

No additional criticality controls are required. Safety is ensured by physical limits on material accumulation, not administrative controls.

---

## Table of Contents

1. [References](#1-references)
2. [Purpose](#2-purpose)
3. [Inputs](#3-inputs)
4. [Modeling Assumptions](#4-modeling-assumptions)
5. [Methodology](#5-methodology)
6. [Results](#6-results)
7. [Accumulation Analysis](#7-accumulation-analysis)
8. [Safety Margin](#8-safety-margin)
9. [Conclusions](#9-conclusions)

**Appendices**
- [A: Geometry Validation](#appendix-a-geometry-validation)
- [B: Density Calculations](#appendix-b-density-calculations)
- [C: Accumulation Calculation](#appendix-c-accumulation-calculation)
- [D: Complete Results Data](#appendix-d-complete-results-data)

---

## 1. References

| Reference | Title |
|-----------|-------|
| OpenMC | Monte Carlo Particle Transport Code, Version 0.15.x |
| ENDF/B-VIII.0 | Evaluated Nuclear Data File, Release VIII.0 |

---

## 2. Purpose

This analysis evaluates criticality safety for the cascade cylinder array by determining:

1. **Critical threshold** — What fill fraction causes criticality? (Sections 5–6)
2. **Maximum accumulation** — What is the maximum credible material buildup? (Section 7)
3. **Safety margin** — Is the margin sufficient for safe-by-design? (Section 8)

Three material scenarios representing upset conditions in a cascade are evaluated:

| Scenario | Material | Scenario |
|----------|----------|---------------|
| UF6 Dry | Solid UF6 | Direct UF6 is deposited in maker |
| UO2F2 Dry | Dry UO2F2 (H/U=0) | UO2F2 is deposited in maker |
| UO2F2 Wet | Wet UO2F2 (H/U=25) | Bounding case of UO2F2 with peak moderation |

---

## 3. Inputs

### 3.1 Array Configuration

| Parameter | Value | Basis |
|-----------|-------|-------|
| Array | 3 × 4 × 5 | Unit cell (rows × cols × layers) |
| Boundary | Reflective | Models infinite array |
| Enrichment | 21 wt% U-235 | HALEU is 20% so we add additional 1% enrichment |

### 3.2 Geometry

![Geometry Cross-Sections](_validation/geometry.png)

*Figure 3.1: Unit cell geometry. Left: XY plane (top view). Right: XZ plane (side view). Note top and bottom caps are not shown because of pixel fidelity but they are there* 

### 3.3 Cylinder Dimensions

| Parameter | Value | Units |
|-----------|-------|-------|
| Inner diameter | 25.4 | cm |
| Internal height | 100.0 | cm |
| Wall thickness | 0.3175 | cm |
| Horizontal gap | 12.7 | cm |
| Vertical gap | 7.62 | cm |
| **Internal volume** | **50,671** | **cm³** |

### 3.4 Material Properties

| Material | Density (g/cc) |
|----------|----------------|
| UF6 (solid) | 5.09 | 
| UO2F2 (dry) | 6.37 | 
| UO2F2 (H/U=25) | 1.95 |

**Note:** UF6, UO2F2 (dry) densities reported from Wikipedia. UO2F2 wet density calculated from ideal mixing (see Appendix B). 

---

## 4. Modeling Assumptions
We setup an infinite array of casettes and make several conservative modeling assumptions to assess criticality.

### 4.1 Conservative Assumptions

| # | Assumption | Justification |
|---|------------|---------------|
| 1 | Infinite array (reflective BC) | Bounds any finite array configuration |
| 2 | 21 wt% enrichment | Maximum credible HALEU for this process |
| 4 | H/U = 25 for wet UO2F2 | Peak moderation ratio (Section 6.2) |
| 5 | All water ingress reacts to UO2F2 and deposits in machine | Bounds water ingress and UO2F2 formation |
| 6 | 10-year equipment lifetime | Full design life |
| 7 | All machines accumulate uniformly | In practice, only failed seals leak and accumulate fissile material significantly. |

---

## 5. Methodology

### 5.1 Approach

1. Run Monte Carlo simulations sweeping fill fraction (α) for each material
2. Identify critical threshold: fill fraction where k-eff + 2σ ≥ 0.95
3. Convert threshold to mass (kg)
4. Compare to maximum credible accumulation
5. Calculate safety margin

### 5.2 Monte Carlo Parameters

| Parameter | Value |
|-----------|-------|
| Code | OpenMC v0.15.x |
| Nuclear data | ENDF/B-VIII.0 |
| Particles per batch | 10,000 |
| Total batches | 150 (50 inactive) |

**Safety Classification:**
- SAFE: k-eff + 2σ < 0.95
- MARGINAL: 0.95 ≤ k-eff + 2σ < 1.00
- CRITICAL: k-eff + 2σ ≥ 1.00

### 5.3 Fill Fraction (α)

Fill fraction α is the fraction of cylinder volume occupied by fissile material:

$$\alpha = \frac{V_{fissile}}{V_{cylinder}}$$

At fill fraction α, the fissile mass per cylinder is:

$$m = \alpha \times V_{cylinder} \times \rho$$

---

## 6. Results

### 6.1 k-effective vs Fill Fraction

#### UF6 Dry

| fill (%) | k-eff + 2σ | Status |
|-------|------------|--------|
| 1% | 0.772 | SAFE |
| 2% | 0.960 | MARGINAL |
| 5% | 1.139 | CRITICAL |
| 10% | 1.220 | CRITICAL |
| 20% | 1.266 | CRITICAL |

#### UO2F2 Dry (H/U = 0)

| fill (%) | k-eff + 2σ | Status |
|-------|------------|--------|
| 1% | 0.885 | SAFE |
| 2% | 1.062 | CRITICAL |
| 5% | 1.223 | CRITICAL |
| 10% | 1.296 | CRITICAL |
| 20% | 1.341 | CRITICAL |

#### UO2F2 Wet (H/U = 25, Bounding)

| fill (%) | k-eff + 2σ | Status |
|-------|------------|--------|
| 2.0% | 0.846 | SAFE |
| 2.5% | 0.953 | MARGINAL |
| 3.0% | 1.037 | CRITICAL |

### 6.2 H/U Ratio Optimization

Peak reactivity occurs at **H/U = 25** (k-eff = 1.650 at 100% fill). This ratio is used for the bounding wet UO2F2 analysis.

| H/U | k-eff + 2σ |
|-----|------------|
| 0 | 1.387 |
| 20 | 1.649 |
| **25** | **1.652** |
| 30 | 1.649 |
| 50 | 1.605 |

### 6.3 Combined Results

![Combined Fill Sweep](summary_plots/combined_fill_sweep.png)

*Figure 6.1: k-effective + 2σ vs fill fraction for all three material scenarios. Horizontal lines show safety limit (0.95) and critical (1.00). Vertical line shows maximum credible accumulation (0.29%).*

### 6.4 Critical Thresholds

| Material | Critical α | Mass per Cylinder |
|----------|------------|-------------------|
| UF6 Dry | ~2% | 5.2 kg UF6 |
| UO2F2 Dry | ~1.5% | 4.8 kg UO2F2 |
| UO2F2 Wet (H/U=25) | ~2.5% | 2.5 kg mixture |

---

## 7. Accumulation Analysis

### 7.1 Mechanism

UO2F2 forms when humid air leaks into UF6-containing equipment:

$$\text{UF}_6 + 2\text{H}_2\text{O} \rightarrow \text{UO}_2\text{F}_2 + 4\text{HF}$$

### 7.2 Input Parameters

| Parameter | Value | Basis |
|-----------|-------|-------|
| Leak rate | 0.01 torr/min | Conservative differential pressure (provided by Riane and Wisher)|
| Humidity | 100% relative humidity | Bounding |
| Temperature | 25°C | Ambient |
| Equipment volume | 12 L | Equipment spec |
| Lifetime | 10 years | Design life |

### 7.3 Result

| Parameter | Value |
|-----------|-------|
| UO2F2 accumulated per machine | **163.6 g** |
| Water associated (H/U=25) | **119.6 g** |
| Total wet mixture mass | **283.2 g** |
| Mixture volume (at 1.95 g/cc) | **145.2 cc** |
| Fill fraction | **0.29%** |

See Appendix C for full calculation.

### 7.4 UF6 Accumulation

Per process engineering, the maximum UF6 holdup at any given time is conservatively **5 g** per machine.

| Parameter | Value |
|-----------|-------|
| UF6 max per machine | **5 g** |
| Fill fraction | **0.002%** |

---

## 8. Safety Margin

| Material | Critical Threshold | Max Accumulation | Margin |
|----------|-------------------|------------------|--------|
| UF6 Dry | 2% (5.2 kg) | 5 g | **1,040×** |
| UO2F2 Wet | 2.5% (2.5 kg) | 283 g (0.29%) | **8.6×** |

**Bounding Case:** UO2F2 wet at H/U=25 with **8.6× safety margin**. UF6 has an even larger margin (1,040×) but UO2F2 wet is the limiting scenario.

---

## 9. Conclusions

**The cascade cylinder array is safe by design.** (See Executive Summary)

| Scenario | Critical Threshold | Max Accumulation | Margin |
|----------|-------------------|------------------|--------|
| UF6 Dry | 5.2 kg | 5 g (operating limit) | **1,040×** |
| UO2F2 Wet | 2.5 kg | 283 g (lifetime accumulation) | **8.6×** |

**Key points:**
- UO2F2: Even if all water deposits and reacts over 10 years at peak moderation (H/U=25), accumulation is 8.6× below critical
- UF6: Operating limit is 1,000× below critical, and would require solidification and continuous accumulation

**Recommendations:**
1. No additional criticality controls required
2. Maintain existing leak-tightness verification program
3. Obtain chemistry SME validation of material properties (Section 4.2)

---

## Appendix A: Geometry Validation

Location: `_validation/` and `summary_plots/`

| File | Description |
|------|-------------|
| `geometry.png` | XY and XZ cross-sections |
| `geometry_thick_wall.png` | Enhanced view with visible caps |

---

## Appendix B: Density Calculations

### B.1 UO2F2 Wet Density (Ideal Mixing)

When UO2F2 is hydrated, the mixture density is:

$$\rho_{mixture} = \frac{M_{UO_2F_2} + n_{H_2O} \times M_{H_2O}}{V_{UO_2F_2} + n_{H_2O} \times V_{H_2O}}$$

Where:
- $n_{H_2O} = \frac{H/U}{2}$ (moles water per mole UO2F2)
- $M_{UO_2F_2} = 308.03$ g/mol
- $M_{H_2O} = 18.02$ g/mol
- $V_{UO_2F_2} = \frac{308.03}{6.37} = 48.35$ cc/mol
- $V_{H_2O} = \frac{18.02}{1.00} = 18.02$ cc/mol

### B.2 Calculated Densities

| H/U | n_H2O | Mass (g) | Volume (cc) | ρ (g/cc) |
|-----|-------|----------|-------------|----------|
| 0 | 0 | 308.03 | 48.35 | 6.37 |
| 10 | 5.0 | 398.13 | 138.45 | 2.88 |
| 20 | 10.0 | 488.23 | 228.55 | 2.14 |
| **25** | **12.5** | **533.28** | **273.60** | **1.95** |
| 30 | 15.0 | 578.33 | 318.65 | 1.82 |

### B.3 Mass Conversion

Fissile mass at fill fraction α:

$$m = \alpha \times 50,671 \text{ cm}^3 \times \rho$$

| Material | ρ (g/cc) | Mass at 1% fill |
|----------|----------|-----------------|
| UF6 | 5.09 | 2.58 kg |
| UO2F2 dry | 6.37 | 3.23 kg |
| UO2F2 wet (H/U=25) | 1.95 | 0.99 kg |

---

## Appendix C: Accumulation Calculation

### C.1 Water Ingress Rate

Water mole fraction in saturated air:
$$f_{H_2O} = \frac{RH \times P_{sat}}{P_{atm}} = \frac{1.0 \times 23.8}{760} = 0.0313$$

Water partial pressure rise rate:
$$\frac{dP_{H_2O}}{dt} = 0.0313 \times 0.01 = 3.13 \times 10^{-4} \text{ torr/min}$$

### C.2 Lifetime Accumulation

Lifetime in minutes:
$$t = 10 \times 365 \times 24 \times 60 = 5,256,000 \text{ min}$$

Total water pressure:
$$\Delta P_{H_2O} = 3.13 \times 10^{-4} \times 5,256,000 = 1,646 \text{ torr} = 2.17 \text{ atm}$$

Moles of water (ideal gas law):
$$n_{H_2O} = \frac{2.17 \times 12}{0.0821 \times 298.15} = 1.06 \text{ mol}$$

### C.3 UO2F2 Formation

From stoichiometry (UF6 + 2H2O → UO2F2 + 4HF):
$$n_{UO_2F_2} = \frac{1.06}{2} = 0.531 \text{ mol}$$

$$m_{UO_2F_2} = 0.531 \times 308.03 = \mathbf{163.6 \text{ g}}$$

### C.4 Wet Mixture at H/U=25

At peak moderation (H/U=25), each mole of UO2F2 is associated with 12.5 moles of water:

$$m_{H_2O} = 0.531 \times 12.5 \times 18.015 = 119.6 \text{ g}$$

Total wet mixture mass:
$$m_{mixture} = 163.6 + 119.6 = \mathbf{283.2 \text{ g}}$$

### C.5 Fill Fraction

Using wet UO2F2 density at H/U=25 (from ideal mixing, see Section 4.2):
$$\rho_{H/U=25} = 1.95 \text{ g/cc}$$

$$V_{mixture} = \frac{283.2}{1.95} = 145.2 \text{ cc}$$

$$\alpha = \frac{145.2}{50,671} = 0.00287 = \mathbf{0.29\%}$$

---

## Appendix D: Complete Results Data

Location: `runs/*/latest/results.csv`

| Run | Description | Cases |
|-----|-------------|-------|
| `uf6_dry_low_fill` | UF6 at 1-20% fill | 6 |
| `uo2f2_dry_low_fill` | UO2F2 dry at 1-20% fill | 6 |
| `uo2f2_hu_sweep` | H/U sweep at 100% fill | 11 |
| `uo2f2_wet_peak` | UO2F2 H/U=25 at 2-3% fill | 3 |

---

*End of Document*
