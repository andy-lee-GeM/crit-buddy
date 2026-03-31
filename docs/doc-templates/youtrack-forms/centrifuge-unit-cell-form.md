# Criticality Analysis Request: Centrifuge Unit Cell

## Scenario

Canonical single-centrifuge unit-cell model with reflective square-cell boundaries.
This request is for the maintained `centrifuge-unit-cell` model, not the older
maker-array or Steven film naming.

## What This Model Currently Explores

- Vessel height
- Fill height inside the vessel
- Enrichment

## Fixed in the Current Certified Model

- Fuel radius is fixed at `11.70 cm`
- Water film outer radius is fixed at `12.70 cm`
- Outer steel radius is fixed at `13.0175 cm`
- Wall thickness is fixed at `0.3175 cm`
- End-cap thickness is fixed at `0.3175 cm`
- Wall material is fixed to stainless steel
- Air, water, and reflected unit-cell boundaries follow the current certified baseline

If you want to study radius, wall thickness, annulus thickness, or material
changes, that is a **model generalization request**, not just a new sweep on
the current certified template.

## Instructions

1. Copy this issue to a working ticket. Do not edit the template directly.
2. Fill in the **Design Inputs** table below.
3. Use `[value1, value2, ...]` for parameter sweeps.
4. Move the working ticket to **Ready for run** when complete.
5. Use the notes section to call out any requested geometry expansion beyond the current model.

## Design Inputs

| Parameter | Value | Notes |
|-----------|-------|-------|
| `enrichment_pct` | | U-235 weight percent enrichment |
| `vessel_height_cm` | | Total vessel height from bottom to top (default model basis: `100.0`) |
| `fill_z_cm` | | Fill height above vessel bottom; example sweep: `[10.0, 20.0, 30.0, 40.0, 50.0]` |

## Analysis-Managed Assumptions

These are not intended RE inputs on the template:

- UO2F2 chemistry / moderation assumption
- Source placement details
- Boundary condition overrides
- Internal air / water material definitions

## Notes

- This model is deck-specific. The radial geometry is fixed by the canonical parity geometry.
- Current certification checkpoint:
  `certifications/centrifuge-unit-cell/2026-03-30-r1/`

## Outputs

Typical outputs attached back to the working ticket:

- `results.csv`
- `REPORT.md`
- plots generated for the requested sweep

---

**Model:** `centrifuge-unit-cell`
