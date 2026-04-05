# Criticality Analysis Request: Cylinder Array

## Model Scope

Finite array of closed centrifuge-style cylinders with explicit cylinder counts
and uniform wall-to-wall gaps. This model reuses the maintained
`centrifuge-unit-cell` vessel geometry as a building block in a 3D rectangular
arrangement.

For the full model writeup, assumptions, and coordinate system, see
`models/cylinder-array/MODEL.md`.

## Visualization

*(No visualization available yet - see visualization_config.yaml to generate)*

Preview can be generated from
`models/cylinder-array/openmc/visualization_config.yaml` using `--validate`.

## Design Inputs

### Material Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `fissile_material` | | `uf6` or `uo2f2` (default: `uo2f2`) |
| `enrichment_pct` | | U-235 weight percent enrichment (default: `20.2`) |
| `h_to_u` | | Hydrogen to uranium atomic ratio for UO2F2 cases (default: `5.0`) |
| `fissile_density_g_cm3` | | Optional density override; for UO2F2 derived from h_to_u (default: `None`) |

### Vessel Geometry (per cylinder)

Reuses `centrifuge-unit-cell` vessel geometry:

| Parameter | Value | Notes |
|-----------|-------|-------|
| `inner_radius_cm` | | Inner fuel radius of the centrifuge vessel (default: `11.70`) |
| `water_film_thickness_cm` | | Water-film thickness outside the fuel region (default: `1.0`) |
| `wall_thickness_cm` | | Steel wall thickness; end-cap thickness follows this value (default: `0.3175`) |
| `vessel_height_cm` | | Total vessel height from bottom to top (default: `100.0`) |
| `fill_height_cm` | | Fill height above vessel bottom; use `[value1, value2, ...]` for sweeps (default: `20.0`) |

### Array Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| `num_cylinders_x` | | Number of cylinders in horizontal (x) direction (default: `3`) |
| `num_cylinders_y` | | Number of cylinders in vertical (y) direction (default: `2`) |
| `num_cylinders_z` | | Number of cylinders in depth (z) direction (default: `3`) |
| `wall_to_wall_gap_cm` | | Uniform edge-to-edge gap between adjacent cylinders; use `[value1, value2, ...]` for sweeps (default: `[0.0, 1.0, 5.0]`) |
| `edge_moderator_thickness_cm` | | Water moderator shell thickness surrounding the entire array (default: `50.0`) |

### Boundary Conditions

| Parameter | Value | Notes |
|-----------|-------|-------|
| `x_boundary_type` | | `vacuum` or `reflective` (default: `vacuum`) |
| `y_boundary_type` | | `vacuum` or `reflective` (default: `vacuum`) |
| `z_boundary_type` | | `vacuum` or `reflective` (default: `vacuum`) |

## Coordinate System

User-facing axes:
- **x**: horizontal
- **y**: vertical
- **z**: depth

The cylinder axis is vertical (aligned with y). Internally, OpenMC keeps the
vessel axis aligned with the OpenMC z-axis and remaps user y/z accordingly.

## Standard Analysis Workflow

For consistency with CB-11/CB-12 analyses, follow this 4-step workflow:

1. **UF6 Dry Screening** (`01_uf6_dry.yaml`): Screen UF6 dry fill conditions across gap and wall thickness
2. **H/U Optimization** (`02_hu_opt.yaml`): Find peak H/U moderation for UO2F2 using worst-case geometry from step 1
3. **Wet Bottom Fill** (`03_wet_bottom_fill.yaml`): Generate 2D heatmap of fill fraction vs gap at peak H/U
4. **UO2F2 Bounding** (`04_uo2f2_bounding.yaml`): Single bounding case with reflective boundaries

See `models/cylinder-array/REQUEST_TEMPLATE.md` for complete config examples.

## Analyst-Managed Assumptions

These are not intended RE inputs on the template:

- UO2F2 chemistry / moderation details beyond h_to_u
- Source placement details
- Internal air / water material definitions
- Wall material selection (currently fixed to stainless steel 316)

## References

- Request template with CB-11/CB-12 format:
  `models/cylinder-array/REQUEST_TEMPLATE.md`
- Copy-paste study config:
  `models/cylinder-array/openmc/example_config.yaml`
- Validation preview config:
  `models/cylinder-array/openmc/visualization_config.yaml`
- Model documentation:
  `models/cylinder-array/MODEL.md`
- Integration test:
  `tests/integration/models/test_cylinder_array.py`

## Instructions

1. Copy this issue to a working ticket. Do not edit the template directly.
2. Fill in the **Design Inputs** tables above with specific values.
3. Use `[value1, value2, ...]` notation for parameter sweeps.
4. For standard workflow, consider running all 4 config steps (see REQUEST_TEMPLATE.md).
5. Add any design rationale, expected limits, or geometry notes below.
6. Move the working ticket to **Ready for run** when complete.

## Notes

## Outputs

Typical outputs attached back to the working ticket:

- `CB-XX-summary.md` - Visual summary with key findings, plots, and safety margin table
- `all_results.csv` - Full case-by-case results
- `bounding_analysis.json` - Bounding calculation artifact
- `REPORT.md` - Detailed experiment report
- Generated plots (H/U optimization, k-eff heatmaps, parameter sweeps)

When a cylinder-array ticket also depends on a per-cylinder allowable-fill
interpolation from the same geometry basis, include that allowable-fill summary
in `REPORT.md`. At minimum capture the interpolation basis, allowable fill
percent, allowable fill height, and liters / kilograms for UF6 and wet UO2F2.

---

**Model:** `cylinder-array`
