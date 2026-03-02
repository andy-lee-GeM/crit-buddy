---
name: crit-independent-review
description: Create a tight, MCNP‑reproducible independent review report for crit-buddy experiments. Use when asked to package assumptions and key modeling parameters (with source files) into a concise PDF and report directory under `reports/`.
---

# Crit Independent Review

## Overview
Produce a minimal, readable report package that lets a criticality engineer reproduce the OpenMC setup in MCNP without including MCNP inputs or data libraries. The report is short, table‑driven, and backed by the Python source‑of‑truth files.

## Output Layout
Create a single report folder:
- `reports/<report_name>/report.md`
- `reports/<report_name>/report.pdf`
- `reports/<report_name>/inputs/*.yaml`
- `reports/<report_name>/plots/geometry.png`
- `reports/<report_name>/source/cylinder_template.py`
- `reports/<report_name>/source/cylinder_openmc_model.py`
- `reports/<report_name>/source/materials.py`

Do not include MCNP inputs, case matrices, or nuclear data files.

## Report Template (Tight)
Use short tables and simple narrative. No derived geometry section.

### Header (bullet list)
- Report name
- Date
- Prepared by
- Units
- Solver basis (reference `templates/cylinder/openmc/model.py`)
- Nuclear data (library name only, no full path)
- Temperature

### Section 1: Overview (narrative + geometry image)
- One paragraph describing the array and boundary conditions
- Short bullet list of case families (e.g., dry UF6, wet UO2F2, H/U sweep)
- Include `plots/geometry.png` here only

### Section 2: Common Geometry Inputs (table)
- rows/cols/layers, radius, height, wall thickness/material, gaps, environment, boundary, reflector thickness

### Section 3: Materials Summary (table)
- UF6, UO2F2, steel, humid air
- One‑line composition basis references to `materials.py` functions
- Thermal scattering note
- Add **UO2F2 H/U density table** as a fixed‑width text block for PDF readability

### Section 4: Physics and Run Settings (table)
- Run mode, particles, batches, inactive/active, total histories
- Source box bounds
- MCNP KCODE/KSRC guidance (one line)

### Section 5: Assumptions and Limits (bullets)
- Room temperature, no burnup, no absorber credit, flat end caps

### Section 6: Source of Truth (bullets)
- List the three Python files included under `source/` (flat, no subdirectories)

## Data Handling Rules
- Remove full paths to cross‑section files; include only library name (e.g., ENDF/B‑VII.1).
- Keep tables short; no nested bullets.
- Avoid duplicate geometry plot sections.

## PDF Generation
Run from inside the report directory so relative image paths resolve:
```bash
cd reports/<report_name>
pandoc report.md -o report.pdf
```

## Call Out Missing Data
If OpenMC or MCNP version is not recorded, list it as an open question at the end of the report.
