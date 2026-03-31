# Criticality Analysis Request: Pipe Cross Model

## Model

Orthogonal pipe-crossing unit-cell request for the maintained
`pipe-cross-model`. This is the current reflected crossing model used for AD-7
style parity and follow-on sweep work.

## Visualization

![Pipe cross geometry preview](assets/pipe-cross-model-geometry.png)

Preview generated from
`models/pipe-cross-model/openmc/visualization_config.yaml` using `--validate`.

## Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `cross_mode` | | `xz` or `xyz` (default: `xz`) |
| `enrichment_pct` | | U-235 weight percent enrichment (default: `20.2`) |
| `pipe_size` | | Standard NPS size or `custom` (default: `custom`) |
| `pipe_outer_radius_cm` | | Used when `pipe_size=custom` (default: `5.715`) |
| `pipe_wall_thickness_cm` | | Used when `pipe_size=custom` (default: `0.3048`) |
| `wall_material` | | `aluminum` or `ss304` (default: `aluminum`) |
| `separation_cm` | | Edge-to-edge separation to neighboring crossings; example sweep: `[0.0, 5.8, 6.5, 7.0]` |
| `gas_core_radius_cm` | | Open inner bore radius after any retained deposit is accounted for |
| `fuel_outer_radius_cm` | | Outer radius of the retained fissile annulus / deposit region |

## Certified Baseline

- `cross_mode = xz`
- `pipe_size = custom`
- `pipe_outer_radius_cm = 5.715`
- `pipe_wall_thickness_cm = 0.3048`
- `gas_core_radius_cm = 4.4102`
- `fuel_outer_radius_cm = 5.4102`
- `separation_cm = 7.0`
- `wall_material = aluminum`
- `enrichment_pct = 20.2`
- Reflected unit-cell boundaries follow the certified baseline

These baseline values reproduce the current blessed parity checkpoint, but the
geometry inputs above are the intended RE-facing sweep surface.

## Instructions

1. Copy this issue to a working ticket. Do not edit the template directly.
2. Fill in the **Parameters** table.
3. Use `[value1, value2, ...]` for parameter sweeps.
4. Add any geometry uncertainty or deposit interpretation notes below.
5. Move the working ticket to **Ready for run** when complete.

## Notes

- `fuel_outer_radius_cm` must not exceed the pipe inner radius.
- `gas_core_radius_cm` must be smaller than `fuel_outer_radius_cm`.
- Copy-paste study config:
  `models/pipe-cross-model/openmc/example_config.yaml`
- Validation preview config:
  `models/pipe-cross-model/openmc/visualization_config.yaml`
- Current certification checkpoint:
  `certifications/pipe-cross-model/2026-03-30-r1/results.md`

## Outputs

Typical outputs attached back to the working ticket:

- `results.csv`
- `REPORT.md`
- plots generated for the requested sweep

---

**Model:** `pipe-cross-model`
