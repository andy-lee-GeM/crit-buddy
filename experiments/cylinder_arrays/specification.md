# Cylinder Array Criticality Analysis

## 1. purpose and scope

This analysis evaluates the criticality safety of rectangular arrays of cylindrical containers holding gaseous UF6. The objective is to determine safe geometry limits (array size, pitch) for storage configurations under normal and credible abnormal conditions.

Results from this analysis support the Integrated Safety Analysis (ISA) for fissile material storage operations.

## 2. system description

The physical system consists of:
- Multiple vertical cylindrical containers arranged in a rectangular array (rows × columns)
- Each container holds gaseous UF6 (uranium hexafluoride)
- Containers are NPS 4" Schedule 10S steel pipes
- The array is surrounded by an environment (air for normal conditions, water for flooding scenarios)

This configuration represents storage of UF6 product cylinders in a controlled area.

## 3. geometry model

### cylinder geometry
| Parameter | Value | Units | Description |
|-----------|-------|-------|-------------|
| Inner radius | 12.7 | cm | NPS 4" pipe inner radius |
| Height | 100.0 | cm | Cylinder height |
| Wall thickness | 0.3175 | cm | Steel wall (Schedule 10S) |

### array configuration
| Parameter | Range | Units | Description |
|-----------|-------|-------|-------------|
| Rows | 2 - 3 | count | Number of rows |
| Columns | 3 - 5 | count | Number of columns |
| Pitch | 7.62 - 20.0 | cm | Gap between outer walls of adjacent cylinders |

### boundary conditions
| Parameter | Value | Units | Description |
|-----------|-------|-------|-------------|
| Environment thickness | 30.0 | cm | Thickness of surrounding material |
| External boundary | Vacuum | - | No reflection beyond environment |

## 4. materials

| Component | Material | Density | Notes |
|-----------|----------|---------|-------|
| Fissile | UF6 (gas) | 5.09 g/cc | Gaseous uranium hexafluoride |
| Wall | Steel | 7.82 g/cc | Carbon steel |
| Environment (normal) | Air | 0.001205 g/cc | Dry air at STP |
| Environment (flooded) | Water | 1.0 g/cc | Full water moderation |

### fissile material specification
| Parameter | Value | Units |
|-----------|-------|-------|
| Enrichment | 20.0 | wt% U-235 |
| UF6 density | 5.09 | g/cc |
| Temperature | 293 | K (room temperature) |

## 5. assumptions and conservatisms

### modeling assumptions
1. Homogeneous UF6 distribution within each cylinder
2. Uniform enrichment across all cylinders
3. All cylinders identical (no manufacturing variations)
4. Cylinders perfectly aligned in rectangular array
5. No intervening structures between cylinders

### conservative assumptions (bounding)
1. **Full water reflection (30 cm)**: Bounds any credible reflector configuration
2. **Maximum credible enrichment**: 20 wt% U-235 (HALEU limit)
3. **Maximum UF6 density**: 5.09 g/cc (near liquid density)
4. **Optimal moderation**: Water flooding scenario captures worst-case moderation
5. **No neutron absorbers**: Credit not taken for structural absorbers

## 6. fixed parameters

| Parameter | Value | Units | Justification |
|-----------|-------|-------|---------------|
| Enrichment | 20.0 | wt% | HALEU maximum |
| Inner radius | 12.7 | cm | NPS 4" pipe |
| Height | 100.0 | cm | Standard container height |
| Wall material | Steel | - | Process specification |
| Wall thickness | 0.3175 | cm | Schedule 10S |
| UF6 density | 5.09 | g/cc | Conservative (near saturation) |
| Boundary thickness | 30.0 | cm | Full reflection |

## 7. varying parameters

| Parameter | Values | Units | Rationale |
|-----------|--------|-------|-----------|
| Rows | 2, 3 | count | Range of credible array sizes |
| Columns | 3, 4, 5 | count | Range of credible array sizes |
| Pitch | 7.62, 8, 10, 12, 14, 16, 17.78, 20 | cm | From touching to well-separated |
| Environment | air, water | - | Normal and flooded conditions |

### parameter matrix
- Total configurations: 2 × 3 × 8 × 2 = **96 cases**

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

A configuration is considered **subcritical** if k-eff + 2σ < 0.95.

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
2. ANSI/ANS-8.7 - Nuclear Criticality Safety in the Storage of Fissile Materials
3. NUREG/CR-6698 - Guide for Validation of Nuclear Criticality Safety Calculational Methodology
