# Cascade Lines Criticality Analysis

## 1. purpose and scope

This analysis evaluates the criticality safety of single cylindrical process pipes (cascade lines) containing gaseous UF6. The objective is to determine safe pipe diameters for centrifuge cascade piping under normal and credible abnormal conditions.

Results from this analysis support the Integrated Safety Analysis (ISA) for enrichment process operations.

## 2. system description

The physical system consists of:
- A single vertical cylindrical pipe containing gaseous UF6
- Pipes are Schedule 10S aluminum process piping
- Pipe sizes range from NPS 1" to NPS 8" (cascade interconnect piping)
- The pipe is surrounded by an environment (air for normal conditions, water for flooding/fire suppression scenarios)

This configuration represents individual cascade line segments in the enrichment process area.

## 3. geometry model

### cylinder geometry
| Parameter | Value | Units | Description |
|-----------|-------|-------|-------------|
| Height | 100.0 | cm | Representative pipe length |
| Wall material | Aluminum | - | Process specification |
| Wall thickness | 0.277 | cm | Conservative (thinnest Sch 10S) |

### pipe sizes (Schedule 10S inner radii)
| NPS | Inner Radius (cm) |
|-----|-------------------|
| 1" | 1.393 |
| 1-1/4" | 1.831 |
| 1-1/2" | 2.136 |
| 2" | 2.739 |
| 2-1/2" | 3.346 |
| 3" | 4.140 |
| 3-1/2" | 4.775 |
| 4" | 5.410 |
| 5" | 6.725 |
| 6" | 8.073 |
| 8" | 10.578 |

### boundary conditions
| Parameter | Value | Units | Description |
|-----------|-------|-------|-------------|
| Reflector thickness | 30.0 | cm | Full reflection |
| External boundary | Vacuum | - | No reflection beyond reflector |

## 4. materials

| Component | Material | Density | Notes |
|-----------|----------|---------|-------|
| Fissile | UF6 (gas) | 5.09 g/cc | Gaseous uranium hexafluoride |
| Wall | Aluminum | 2.70 g/cc | 6061-T6 aluminum |
| Reflector (normal) | Air | 0.001205 g/cc | Dry air at STP |
| Reflector (flooded) | Water | 1.0 g/cc | Full water moderation |

### fissile material specification
| Parameter | Values | Units |
|-----------|--------|-------|
| Enrichment | 5.0 (LEU), 20.0 (HALEU) | wt% U-235 |
| UF6 density | 5.09 | g/cc |
| Temperature | 293 | K (room temperature) |

## 5. assumptions and conservatisms

### modeling assumptions
1. Homogeneous UF6 distribution within the pipe
2. Infinite cylinder approximation (100 cm height with reflected ends)
3. Single isolated pipe (no interaction with adjacent piping)
4. Uniform enrichment along pipe length

### conservative assumptions (bounding)
1. **Full water reflection (30 cm)**: Bounds any credible reflector including fire suppression
2. **Maximum UF6 density**: 5.09 g/cc (near liquid density, bounds process upsets)
3. **Conservative wall thickness**: Uses thinnest Schedule 10S value (0.277 cm)
4. **No neutron absorbers**: Credit not taken for structural absorbers or borated materials

## 6. fixed parameters

| Parameter | Value | Units | Justification |
|-----------|-------|-------|---------------|
| Height | 100.0 | cm | Representative length with reflected ends |
| Wall material | Aluminum | - | Process specification |
| Wall thickness | 0.277 | cm | Conservative (thinnest Sch 10S) |
| UF6 density | 5.09 | g/cc | Conservative (near saturation) |
| Reflector thickness | 30.0 | cm | Full reflection |

## 7. varying parameters

| Parameter | Values | Units | Rationale |
|-----------|--------|-------|-----------|
| Enrichment | 5.0, 20.0 | wt% | LEU and HALEU operations |
| Inner radius | 1.393 - 10.578 | cm | NPS 1" through NPS 8" |
| Reflector material | air, water | - | Normal and flooded conditions |

### parameter matrix
- Enrichments: 2 (LEU, HALEU)
- Radii: 11 (NPS 1" through NPS 8")
- Reflectors: 2 (air, water)
- Total configurations: 2 × 11 × 2 = **44 cases**

## 8. calculation settings

| Parameter | Value | Description |
|-----------|-------|-------------|
| Particles per batch | 10,000 | Neutrons per generation |
| Inactive batches | 50 | Source convergence |
| Active batches | 100 | Statistics accumulation |
| Total batches | 150 | Inactive + active |

### convergence criteria
- Shannon entropy of fission source converged before active batches
- k-eff standard deviation < 0.001 (typical)

## 9. acceptance criteria

| Criterion | Limit | Basis |
|-----------|-------|-------|
| k-eff + 2σ | < 0.95 | ANSI/ANS-8.1 subcritical limit with margin |

A pipe diameter is considered **safe** if k-eff + 2σ < 0.95 under all moderation conditions.

## 10. calculation methodology

### code and data
| Item | Value |
|------|-------|
| Transport code | OpenMC (Monte Carlo) |
| Nuclear data | ENDF/B-VIII.0 |
| Code version | OpenMC 0.14.x |

### methodology
1. Continuous-energy Monte Carlo neutron transport
2. k-eigenvalue calculation for multiplication factor
3. Point-wise cross sections at 293K
4. Explicit geometry representation (no homogenization)

## 11. references

1. ANSI/ANS-8.1 - Nuclear Criticality Safety in Operations with Fissionable Materials Outside Reactors
2. ANSI/ANS-8.5 - Use of Borosilicate-Glass Raschig Rings as a Neutron Absorber in Solutions of Fissile Material
3. NUREG/CR-6698 - Guide for Validation of Nuclear Criticality Safety Calculational Methodology
4. Pipe Schedule Reference: ASME B36.19M (Stainless Steel Pipe)
