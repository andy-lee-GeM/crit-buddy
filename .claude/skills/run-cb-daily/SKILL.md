---
name: run-cb-daily
description: Process crit-buddy tickets from YouTrack through the standard 3-step analysis pipeline
argument-hint:
---

# Skill: Run Crit-Buddy Daily

A daily workflow to process criticality modeling requests from YouTrack through the standard analysis pipeline.

## Usage

```
/run-cb-daily              # Process all tickets in READY state
/run-cb-daily CRIT-001     # Process specific ticket
```

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│  1. PULL YOUTRACK                                           │
│     - Get tickets in "Ready" state                          │
│     - Parse ticket description for parameters               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. SETUP EXPERIMENT                                        │
│     - Create experiment directory                           │
│     - Generate config files from ticket parameters          │
│     - Create experiment-plan.md                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. VALIDATE GEOMETRY                                       │
│     - Run --validate to generate geometry plots             │
│     - Review geometry.png in _validation/                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. UPDATE YOUTRACK                                         │
│     - Move ticket to "In Progress"                          │
│     - Attach experiment-plan.md and geometry.png            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  5. REVIEW EXPERIMENT (approval gate)                       │
│     - Run /review-experiment on uf6_dry.yaml                │
│     - Present checklist to user                             │
│     - WAIT FOR USER APPROVAL before proceeding              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  6. RUN ANALYSIS (iterative 3-step pipeline)                │
│     - Step 1: UF6 Dry → find worst-case geometry            │
│     - Step 2: H/U Sweep (at worst-case) → find peak H/U     │
│     - Step 3: Fill Sweep (at worst-case + peak H/U)         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  7. GENERATE REPORT                                         │
│     - Generate summary plots                                │
│     - Generate TICKET_SUMMARY.md                            │
│     - Post summary to YouTrack                              │
│     - Move ticket to "Complete"                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Instructions

### Phase 1: Pull YouTrack

1. Query YouTrack API for tickets with status "Ready":
   ```
   GET /api/issues?query=project:CRIT+State:Ready
   ```

2. For each ticket, read the ticket description to extract parameters from the markdown table.

3. If no tickets in Ready state, report and exit.

### Phase 2: Setup Experiment

For each ticket:

1. **Create directory structure:**
   ```
   experiments/crit_requests/{TICKET_ID}/
   ├── _config/
   ├── _validation/
   ├── runs/           # Created automatically by run_study.py
   └── summary_plots/
   ```

2. **Generate config files** using ticket parameters:

   **`_config/uf6_dry.yaml`** - Geometry sweep (find worst-case):
   ```yaml
   problem: {template}
   name: "{TICKET_ID} - UF6 Dry"

   # Geometry from ticket (may be lists for sweep)
   {geometry_params}

   # Material from ticket
   wall_material: {wall_material}
   wall_thickness_cm: {wall_thickness_cm}

   # Fixed for UF6 dry scenario
   enrichment: {enrichment}
   fissile_material: uf6
   fissile_density: 5.09
   fill_fraction: 1.0
   environment: humid_air
   reflector_thickness_cm: 30
   ```

   **`_config/uo2f2_hu_sweep.yaml`** - H/U optimization (at worst-case geometry):
   ```yaml
   problem: {template}
   name: "{TICKET_ID} - H/U Sweep"

   # IMPORTANT: Use worst-case geometry from Step 1 (single values, not lists)
   # Example: if gap_cm: [5, 10, 15] in Step 1 and gap_cm=5 was worst, use:
   # gap_cm: 5
   {geometry_worst_case}

   # Material from ticket
   wall_material: {wall_material}
   wall_thickness_cm: {wall_thickness_cm}

   # Sweep H/U ratio
   h_to_u: [0, 10, 20, 30, 40, 50]

   # Fixed for UO2F2 scenario
   enrichment: {enrichment}
   fissile_material: uo2f2
   fissile_density: 6.37
   fill_fraction: 1.0
   environment: humid_air
   reflector_thickness_cm: 30
   ```

   **`_config/uo2f2_fill_sweep.yaml`** - Fill threshold (at worst-case geometry + peak H/U):
   ```yaml
   problem: {template}
   name: "{TICKET_ID} - Fill Sweep"

   # IMPORTANT: Use worst-case geometry from Step 1 (single values)
   {geometry_worst_case}

   # Material from ticket
   wall_material: {wall_material}
   wall_thickness_cm: {wall_thickness_cm}

   # Use peak H/U from Step 2 (single value)
   h_to_u: {peak_h_to_u}  # Update after Step 2

   # Sweep fill fraction (0.1 to 1.0 in 0.1 increments)
   fill_fraction: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

   # Fixed for UO2F2 scenario
   enrichment: {enrichment}
   fissile_material: uo2f2
   fissile_density: 6.37
   environment: humid_air
   reflector_thickness_cm: 30
   ```

3. **Create experiment-plan.md** summarizing:
   - Ticket ID and requestor
   - Template and enrichment
   - Geometry parameters being swept
   - 3-step analysis plan

### Phase 3: Validate Geometry

Before running full analysis, validate the geometry is correct:

```bash
python run_study.py experiments/crit_requests/{TICKET_ID}/_config/uf6_dry.yaml --validate
```

This generates:
- `_validation/geometry.png` - 2D cross-section views
- `_validation/voxel_3d.png` - 3D visualization (if enabled)

**Review the geometry plots** to ensure:
- Dimensions match ticket parameters
- Materials are correctly assigned
- Array configurations look correct

### Phase 4: Update YouTrack

1. **Move ticket to "In Progress":**
   ```
   POST /api/issues/{TICKET_ID}/commands
   Body: {"query": "State In Progress"}
   ```

2. **Attach experiment plan and geometry:**
   ```
   POST /api/issues/{TICKET_ID}/attachments
   Files: experiment-plan.md, _validation/geometry.png
   ```

3. **Add comment:**
   ```
   POST /api/issues/{TICKET_ID}/comments
   Body: "Experiment setup complete. Geometry validated. Ready for review."
   ```

### Phase 5: Review Experiment (Approval Gate)

**IMPORTANT: Do not proceed to Phase 6 without explicit user approval.**

1. **Run the review skill** on the UF6 dry config:
   ```
   /review-experiment experiments/crit_requests/{TICKET_ID}/_config/uf6_dry.yaml
   ```

2. **Present the review checklist** covering:
   - Geometry visualization (does it look correct?)
   - Parameter configuration (are ranges appropriate?)
   - Conservative assumptions (full reflection, optimal moderation?)
   - Materials (correct UF6/UO2F2 definitions?)
   - Simulation quality (sufficient particles for convergence?)

3. **Ask the user for approval** using AskUserQuestion:
   ```
   "Ready to start the 3-step analysis pipeline for {TICKET_ID}?"

   Options:
   - "Approved - Start analysis"
   - "Changes needed" (user provides feedback)
   - "Cancel"
   ```

4. **If changes requested:**
   - Make the requested modifications to config files
   - Re-run `--validate` if geometry changed
   - Return to step 1 and re-review

5. **If approved:**
   - Proceed to Phase 6

### Phase 6: Run Analysis (Iterative 3-Step Pipeline)

**IMPORTANT: This is an iterative process. Each step informs the next.**

**Step 1: UF6 Dry - Find Worst-Case Geometry**

```bash
python run_study.py experiments/crit_requests/{TICKET_ID}/_config/uf6_dry.yaml
```

Output: `runs/uf6_dry/{timestamp}/results.csv`

**After Step 1:**
- Review results.csv to find the geometry with **highest k-eff**
- This is the **worst-case geometry** for criticality
- Update `uo2f2_hu_sweep.yaml` and `uo2f2_fill_sweep.yaml` with these fixed values

Example: If sweeping `gap_cm: [5, 10, 15, 20]` and `gap_cm=5` gives highest k-eff:
```yaml
# In uo2f2_hu_sweep.yaml and uo2f2_fill_sweep.yaml:
gap_cm: 5  # Fixed at worst-case (was [5, 10, 15, 20])
```

**Step 2: H/U Sweep - Find Peak Moderation**

```bash
python run_study.py experiments/crit_requests/{TICKET_ID}/_config/uo2f2_hu_sweep.yaml
```

Output: `runs/uo2f2_hu_sweep/{timestamp}/results.csv`

**After Step 2:**
- Review results.csv to find the H/U ratio with **highest k-eff**
- This is the **peak H/U** (optimal moderation)
- Update `uo2f2_fill_sweep.yaml` with this fixed value

Example: If `h_to_u=20` gives highest k-eff:
```yaml
# In uo2f2_fill_sweep.yaml:
h_to_u: 20  # Fixed at peak (was [0, 10, 20, 30, 40, 50])
```

**Step 3: Fill Sweep - Find Critical Threshold**

```bash
python run_study.py experiments/crit_requests/{TICKET_ID}/_config/uo2f2_fill_sweep.yaml
```

Output: `runs/uo2f2_fill_sweep/{timestamp}/results.csv`

**After Step 3:**
- Review results.csv to find the **critical threshold**
- This is the fill fraction where k-eff + 2σ ≥ 0.95
- If all fill fractions are SAFE, the configuration is safe-by-design

### Phase 7: Generate Report

After all runs complete:

1. **Generate summary plots** from `runs/*/results.csv`

2. **Generate TICKET_SUMMARY.md** with:
   - Safety finding (1-line conclusion)
   - Status table (SAFE/MARGINAL/CRITICAL for each scenario)
   - Critical threshold (fill % where system becomes unsafe)
   - Worst-case geometry parameters
   - Peak H/U ratio
   - Results tables and plots

3. **Update YouTrack:**
   - Post summary as comment
   - Attach TICKET_SUMMARY.md and summary plots
   - Move ticket to "Complete"

---

## Directory Structure After Run

```
experiments/crit_requests/{TICKET_ID}/
├── _config/
│   ├── uf6_dry.yaml           # Geometry sweep config
│   ├── uo2f2_hu_sweep.yaml    # H/U sweep (updated with worst-case geometry)
│   └── uo2f2_fill_sweep.yaml  # Fill sweep (updated with worst-case + peak H/U)
├── _validation/
│   ├── geometry.png           # 2D cross-sections
│   └── voxel_3d.png           # 3D visualization
├── runs/
│   ├── uf6_dry/
│   │   └── {timestamp}/
│   │       ├── config.yaml
│   │       ├── results.csv
│   │       └── cases/
│   ├── uo2f2_hu_sweep/
│   │   └── {timestamp}/
│   │       ├── config.yaml
│   │       ├── results.csv
│   │       └── cases/
│   └── uo2f2_fill_sweep/
│       └── {timestamp}/
│           ├── config.yaml
│           ├── results.csv
│           └── cases/
├── summary_plots/
│   ├── uf6_dry_geometry.png
│   ├── hu_sweep.png
│   └── fill_sweep.png
├── experiment-plan.md
└── TICKET_SUMMARY.md
```

---

## Safety Classification

| Status | Criteria | Meaning |
|--------|----------|---------|
| **SAFE** | k-eff + 2σ < 0.95 | System is subcritical with margin |
| **MARGINAL** | 0.95 ≤ k-eff + 2σ < 1.0 | System is subcritical but close to critical |
| **CRITICAL** | k-eff + 2σ ≥ 1.0 | System may be critical |

---

## Common Templates

| Template | Description | Key Geometry Params |
|----------|-------------|---------------------|
| `cylinder` | Single or 3D array of vertical cylinders | radius_cm, height_cm, rows, cols, layers, gap_horizontal_cm, gap_vertical_cm |
| `pipe` | Single or 2D array of horizontal pipes | pipe_size, length_cm, rows, cols, gap_cm |
| `rectangular_box` | Rectangular parallelepiped | length_cm, width_cm, height_cm |
| `shipping_cylinder` | Single ANSI cylinder | cylinder_type (30B, 48Y, etc.) |
| `cascade_array` | Hierarchical cascade layout | Template-specific parameters |

---

## Iterative Workflow Summary

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         ITERATIVE SAFETY CASE                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Step 1: UF6 Dry                                                           │
│  ├─ Sweep: gap_cm: [5, 10, 15, 20]                                         │
│  ├─ Output: k-eff for each gap                                             │
│  └─ Find: WORST-CASE GEOMETRY → gap_cm = 5 (highest k-eff)                 │
│                    ↓                                                       │
│  Step 2: H/U Sweep                                                         │
│  ├─ Fixed: gap_cm: 5 (worst-case from Step 1)                              │
│  ├─ Sweep: h_to_u: [0, 10, 20, 30, 40, 50]                                 │
│  ├─ Output: k-eff for each H/U                                             │
│  └─ Find: PEAK H/U → h_to_u = 20 (highest k-eff)                           │
│                    ↓                                                       │
│  Step 3: Fill Sweep                                                        │
│  ├─ Fixed: gap_cm: 5 (worst-case), h_to_u: 20 (peak)                       │
│  ├─ Sweep: fill_fraction: [0.1, 0.2, ..., 1.0]                             │
│  ├─ Output: k-eff vs fill                                                  │
│  └─ Find: CRITICAL THRESHOLD → fill where k-eff + 2σ ≥ 0.95               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

**Key Insight:** Each step uses fixed values from the previous step. We're finding the bounding case (worst geometry, peak moderation) before determining the safety threshold.
