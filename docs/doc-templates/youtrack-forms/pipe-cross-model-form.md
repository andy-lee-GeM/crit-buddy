# Criticality Analysis Request: Pipe Cross Model

## Scenario

Orthogonal pipe-crossing unit-cell request for the maintained
`pipe-cross-model`. This is the current reflected crossing model used for AD-7
style parity and follow-on sweep work.

## What This Model Currently Explores

- Supported crossing modes:
  - `xz`: one x-directed pipe crossing one z-directed pipe
  - `xyz`: mutually orthogonal x/y/z pipes crossing at the origin
- Pipe outer size and wall thickness
- Open bore radius and retained deposit radius
- Separation to neighboring reflected crossings
- Wall material
- Enrichment

## Simplification Rule for RE Use

The RE should describe the **part geometry and materials**:

- crossing type
- pipe size or custom dimensions
- wall material
- minimum spacing
- bore/open-flow radius
- retained deposit extent if known

The RE should **not** be asked to choose H/U, explicit UO2F2 density, source
placement, or boundary-condition details. Those are analysis assumptions owned
by crit-buddy / the analyst.

## Instructions

1. Copy this issue to a working ticket. Do not edit the template directly.
2. Fill in the **Design Inputs** table below.
3. Use `[value1, value2, ...]` for parameter sweeps.
4. Move the working ticket to **Ready for run** when complete.
5. Use the notes section if the deposit geometry is uncertain and needs analyst interpretation.

## Design Inputs

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

## Analysis-Managed Assumptions

These are not intended RE inputs on the template:

- H/U selection
- explicit UO2F2 density entry
- UF6 density overrides
- moderator density overrides
- boundary-condition overrides

## Notes

- `fuel_outer_radius_cm` must not exceed the pipe inner radius.
- `gas_core_radius_cm` must be smaller than `fuel_outer_radius_cm`.
- Current certification checkpoint:
  `certifications/pipe-cross-model/2026-03-30-r1/`

## Outputs

Typical outputs attached back to the working ticket:

- `results.csv`
- `REPORT.md`
- plots generated for the requested sweep

---

**Model:** `pipe-cross-model`
