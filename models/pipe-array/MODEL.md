# Pipe Array Model

## Overview

Multiple cylindrical pipes arranged in linear array configuration, designed for criticality analysis of piping systems with interaction effects. This model extends the single pipe to analyze spacing requirements.

## Geometry

**Configuration:** N pipes arranged in a line along the x-axis

Each pipe has the same structure as the single pipe model:
1. **Solution region:** UO2F2 solution (center)
2. **Gas gap:** UF6 gas between solution and wall
3. **Pipe wall:** Aluminum
4. **Headspace:** UF6 gas above solution (if partial fill)

**Surrounding region:** Optional water moderator/reflector (default: included)

**Boundaries:** Reflective (default) for infinite array, or vacuum for finite array

**Default Configuration:** 2-pipe array matching MCNP reference case

## Materials

Same as `pipe-unit-cell` model:

- **UO2F2 solution:** 6.37 g/cm³, 20.2% enriched
- **UF6 gas:** 0.0127 g/cm³, 60.4% enriched (headspace/gap)
- **Aluminum:** 2.70 g/cm³ (pipe walls)
- **Water:** 1.0 g/cm³ (optional moderator/reflector)

## Parameters

### Sweep Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `enrichment_pct` | 20.2 | 0.1-100.0 | U-235 enrichment (%) |
| `n_pipes` | 2 | 1-20 | Number of pipes in array |
| `pipe_size` | custom | standard NPS or custom | Standard Schedule 10/10S pipe size |
| `pipe_pitch_cm` | 11.43 | 1.0-100.0 | Center-to-center spacing |
| `edge_spacing_cm` | derived | 0.0-100.0 | Edge-to-edge spacing, overrides pitch when set |
| `pipe_outer_radius_cm` | 5.715 | 0.5-50.0 | Outer radius of pipe |
| `pipe_wall_thickness_cm` | 0.3048 | 0.05-2.0 | Wall thickness |
| `solution_radius_cm` | derived | 0.5-50.0 | Radius of UO2F2 solution |
| `solution_gap_cm` | 1.0 | 0.0-10.0 | Radial UF6 gap from solution to inner wall |
| `pipe_height_cm` | 17.43 | 5.0-200.0 | Total pipe height |
| `fill_fraction` | 1.0 | 0.01-1.0 | Fraction filled |
| `boundary_type` | reflective | reflective/vacuum | Boundary condition |
| `include_water` | true | true/false | Water moderator/reflector |

### Derived Parameters

- **Edge spacing:** pitch - 2 × outer_radius
- **Pitch from edge spacing:** `2 × outer_radius + edge_spacing_cm` when sweeping NPS sizes
- **Pipe centers:** Array positions along x-axis
- **Boundary positions:** Adjusted based on array size

## MCNP Reference

**File:** `../pipe-unit-cell/mcnp/reference.inp`

The MCNP reference case is a **2-pipe infinite lattice** - this is the benchmark configuration for validation.

**MCNP Configuration:**
- 2 pipes: centers at x=0 and x=11.43 cm
- Pitch: 11.43 cm center-to-center
- Edge spacing: ~0 cm (nearly touching!)
- Water moderator/reflector: included
- Reflective boundaries: infinite array

**Expected k-eff:** To be determined from MCNP run

## Validation

### MCNP Benchmark

The 2-pipe default configuration should reproduce the MCNP reference case:

```yaml
model: pipe-array
params:
  n_pipes: 2
  pipe_pitch_cm: 11.43
  include_water: true
  boundary_type: reflective
```

**Acceptance:** OpenMC vs MCNP k-eff agreement within 2-3σ

### Expected Trends

1. **k-eff increases with:**
   - Number of pipes (more fissile mass + interaction)
   - Closer spacing (more neutron interaction)
   - Water moderator (better thermalization)

2. **k-eff decreases with:**
   - Larger edge spacing (less interaction)
   - Vacuum boundaries (less reflection)
   - No water moderator (harder spectrum)

3. **Sensitivity to spacing:**
   - Very sensitive near critical spacing
   - Less sensitive when far apart (isolated pipes)

## Usage

### MCNP Validation Case

```yaml
model: pipe-array
name: MCNP Reference Validation

params:
  n_pipes: 2
  pipe_pitch_cm: 11.43
  enrichment_pct: 20.2
  include_water: true
  boundary_type: reflective
```

### Spacing Sweep

```yaml
model: pipe-array
name: Pipe Spacing Study

params:
  n_pipes: 2
  pipe_size: "4"
  edge_spacing_cm: [0.0, 2.54, 5.08, 10.16, 20.32]
  enrichment_pct: 20.2
  include_water: true
  boundary_type: reflective
```

### Pipe Count Sweep

```yaml
model: pipe-array
name: Array Size Study

params:
  n_pipes: [2, 3, 4, 5]
  pipe_pitch_cm: 20.0
  boundary_type: vacuum
  include_water: false
```

## Typical Applications

1. **MCNP validation** - Benchmark OpenMC against reference case
2. **Spacing studies** - Determine minimum safe edge spacing for criticality
3. **Array size studies** - Analyze reactivity vs number of pipes
4. **NPS sensitivity studies** - Compare standard pipe sizes at common spacing
5. **Water reflection studies** - Compare with/without moderator
6. **Boundary studies** - Infinite array (reflective) vs finite (vacuum)

## Related Models

- **pipe-unit-cell:** Single pipe building block
- **centrifuge-array:** Similar array concept for centrifuges

## Notes

### MCNP Reference Geometry

The MCNP reference has **asymmetric boundaries**:
- X: -8.715 to 8.815 cm
- Y: -8.715 to 20.145 cm

This is preserved exactly for the 2-pipe default case to match MCNP.

### Spacing Considerations

- Default pitch (11.43 cm) has ~0 cm edge-to-edge spacing
- This is very close spacing and likely highly reactive
- For safety studies, sweep to larger spacing to find safe limits

### Water Moderator

The MCNP reference includes water between and around pipes. This is conservative (increases reactivity) for spacing studies.

### Future Extensions

- Grid arrays (crossing pipes in X and Y)
- Triangular pitch (hexagonal packing)
- Variable fill per pipe
- Mixed pipe sizes
