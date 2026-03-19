# Pipe Unit Cell Model

## Overview

Single cylindrical pipe with UO2F2 solution, designed for criticality analysis of piping systems. This model serves as the building block for multi-pipe array studies.

## Geometry

**Configuration:** Vertical cylindrical pipe with three radial regions:

1. **Solution region (center):** UO2F2 solution
   - Default radius: 4.4102 cm
   - Parametric fill fraction (0.0-1.0)

2. **Gas gap:** UF6 gas between solution and pipe wall
   - From solution radius to pipe inner radius
   - Default thickness: 1.0 cm

3. **Pipe wall:** Aluminum
   - Default thickness: 0.3048 cm
   - Default outer radius: 5.715 cm

4. **Headspace:** UF6 gas above solution (if partial fill)

**Boundaries:** Reflective on all sides (default) to simulate infinite lattice, or vacuum for isolated pipe

**Height:** Default 17.43 cm (parametric)

## Materials

All materials match the MCNP reference case (`mcnp/reference.inp`):

### Material 5: UO2F2 Solution
- **Density:** 6.37 g/cm³
- **Composition:** UO₂F₂ stoichiometry (1:2:2 ratio)
- **Enrichment:** 20.2% U-235 (parametric)
- **No hydrogen** - differs from AD-6 optimization

### Material 1: UF6 Gas
- **Density:** 0.0127 g/cm³
- **Composition:** UF₆ stoichiometry (1:6 ratio)
- **Enrichment:** 60.4% U-235 (headspace gas)
- **Location:** Gas gap + headspace above solution

### Material 2: Aluminum
- **Density:** 2.70 g/cm³
- **Composition:** Pure Al-27
- **Location:** Pipe wall

## Parameters

### Sweep Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `enrichment_pct` | 20.2 | 0.1-100.0 | U-235 enrichment (%) |
| `pipe_size` | custom | standard NPS or custom | Standard Schedule 10/10S pipe size |
| `pipe_outer_radius_cm` | 5.715 | 0.5-50.0 | Outer radius of pipe |
| `pipe_wall_thickness_cm` | 0.3048 | 0.05-2.0 | Wall thickness |
| `solution_radius_cm` | derived | 0.5-50.0 | Radius of UO2F2 solution |
| `solution_gap_cm` | 1.0 | 0.0-10.0 | Radial UF6 gap from solution to inner wall |
| `pipe_height_cm` | 17.43 | 5.0-200.0 | Total pipe height |
| `fill_fraction` | 1.0 | 0.01-1.0 | Fraction filled with solution |
| `boundary_type` | reflective | reflective/vacuum | Boundary condition |

### Derived Parameters

The template automatically calculates:
- Inner pipe radius = outer radius - wall thickness
- Solution radius = inner radius - `solution_gap_cm` when not explicitly set
- Fill height = total height × fill fraction
- Fill surface z-position
- Unit cell pitch (extends beyond pipe)

## MCNP Reference

**File:** `mcnp/reference.inp`

The MCNP reference case is a **2-pipe infinite lattice**, not a single pipe. However, the single pipe model uses the same material specifications and dimensions.

**Key reference parameters:**
- Pipe outer radius: 5.715 cm
- Wall thickness: 0.3048 cm
- Solution radius: 4.4102 cm
- UO2F2 density: 6.37 g/cm³
- Enrichment: 20.19%

## Validation

### Expected Trends

Physical validation criteria (no MCNP comparison for single pipe):

1. **k-eff increases with:**
   - Fill fraction (more fissile mass)
   - Pipe diameter (more fissile mass)
   - Enrichment (more U-235)

2. **k-eff decreases with:**
   - Void/vacuum boundaries (less reflection)
   - Thinner solution radius (less fissile mass)

3. **Single pipe should be subcritical** with reflective boundaries at default parameters

### Benchmark Comparison

The 2-pipe MCNP reference case can be used to validate the pipe-array model (see `models/pipe-array/`).

## Usage

### As Model-Based Config

```yaml
model: pipe-unit-cell
name: Single Pipe Parametric Study

params:
  pipe_size: "4"
  fill_fraction: [0.2, 0.5, 0.8, 1.0]
  solution_gap_cm: 1.0
  boundary_type: reflective
```

### Programmatic

```python
from models.pipe_unit_cell import Template
from critbuddy.core.runner import ModelRunner

template = Template()
params = {
    "fill_fraction": 0.5,
    "enrichment_pct": 20.2,
    "boundary_type": "reflective"
}

runner = ModelRunner(template)
result = runner.run(params)
print(f"k-eff: {result.keff:.4f} ± {result.sigma:.4f}")
```

## Typical Applications

1. **Fill fraction studies** - Identify most reactive fill level
2. **NPS studies** - Analyze standard pipe sizes without manual dimension entry
3. **Wall thickness studies** - Determine bounding case
4. **Enrichment sensitivity** - Calculate reactivity coefficients
5. **Boundary condition studies** - Compare reflected vs isolated

## Related Models

- **pipe-array:** Multiple pipes in linear or grid configurations
- **centrifuge-unit-cell:** Similar cylindrical geometry for centrifuge analysis

## Notes

- This model does **not** include hydrogen in UO2F2 (differs from AD-6)
- Composition matches MCNP reference exactly
- Default parameters from MCNP reference case
- Reflective boundaries simulate infinite lattice (conservative for single pipe)
- For realistic single pipe analysis, use `boundary_type: vacuum`
