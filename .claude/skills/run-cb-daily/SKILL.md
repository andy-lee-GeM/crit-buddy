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

1. **Fetch tickets using the unified YouTrack CLI:**
   ```bash
   python scripts/youtrack/youtrack_cli.py fetch-ready
   ```

2. **For a specific ticket:**
   ```bash
   python scripts/youtrack/youtrack_cli.py fetch CB-10 --json
   ```

3. For each ticket, read the ticket description to extract parameters from the markdown table.

4. If no tickets in Ready state, report and exit.

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

Use the unified YouTrack CLI for all operations:

1. **Move ticket to "In Progress":**
   ```bash
   python scripts/youtrack/youtrack_cli.py update-status {TICKET_ID} "In Progress"
   ```

2. **Add comment:**
   ```bash
   python scripts/youtrack/youtrack_cli.py comment {TICKET_ID} "Experiment setup complete. Geometry validated. Ready for review."
   ```

Note: File attachments will be uploaded in Phase 7 along with results.

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

**Step 3: Fill Sweep - ALL Geometries**

**IMPORTANT: Run fill sweep for EACH geometry case from Step 1, not just worst-case.**

1. **Create configs folder for fill sweeps:**
   ```
   _config/uo2f2_fill_sweeps/
   ├── case_1.yaml  # pipe_size=3, gap=0
   ├── case_2.yaml  # pipe_size=3, gap=10
   ├── case_3.yaml  # pipe_size=4, gap=0
   └── ...          # One config per geometry from Step 1
   ```

2. **Each fill sweep config uses:**
   - Fixed geometry from one Step 1 case
   - Peak H/U from Step 2
   - Sweep fill_fraction: [0.1, 0.2, ..., 1.0]

   Example `_config/uo2f2_fill_sweeps/case_1.yaml`:
   ```yaml
   problem: pipe
   name: "{TICKET_ID} - Fill Sweep (3\" pipe, gap=0)"

   # Fixed geometry from Step 1 case
   pipe_size: "3"
   gap_cm: 0
   rows: 2
   cols: 3
   length_cm: 1000

   # Peak H/U from Step 2
   h_to_u: 20

   # Sweep fill fraction
   fill_fraction: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

   # Fixed for UO2F2
   fissile_material: uo2f2
   fissile_density: 6.37
   enrichment: {enrichment}
   environment: humid_air
   reflector_thickness_cm: 30
   ```

3. **Run all fill sweeps:**
   ```bash
   # Run each config - outputs go to runs/uo2f2_fill_sweeps/{timestamp}/case_N/
   for config in experiments/crit_requests/{TICKET_ID}/_config/uo2f2_fill_sweeps/*.yaml; do
       python run_study.py "$config"
   done
   ```

4. **Output structure:**
   ```
   runs/uo2f2_fill_sweeps/{timestamp}/
   ├── all_results.csv      # Combined results from all cases
   ├── case_1/results.csv
   ├── case_2/results.csv
   └── case_N/results.csv
   ```

**After Step 3:**
- Generate overlay plot showing ALL fill% curves:
  ```bash
  python -c "from critbuddy.reporting.summary_plots import generate_fill_overlay_from_runs; generate_fill_overlay_from_runs('experiments/crit_requests/{TICKET_ID}')"
  ```
- The overlay plot shows critical threshold for each geometry
- Identify which geometries are safe-by-design vs. require fill limits

### Phase 7: Generate Report

After all runs complete:

1. **Generate summary plots**:
   ```bash
   PYTHONPATH=/path/to/crit-buddy python -c "
   from critbuddy.reporting.summary_plots import plot_fill_sweep, load_results
   from pathlib import Path
   results = load_results(Path('experiments/crit_requests/{TICKET_ID}/runs/uo2f2_fill_sweep/latest/results.csv'))
   plots_dir = Path('experiments/crit_requests/{TICKET_ID}/results/plots')
   plots_dir.mkdir(parents=True, exist_ok=True)
   plot_fill_sweep(results, plots_dir / 'fill_sweep.png', '{TICKET_ID}: Fill Fraction Sweep')
   "
   ```

2. **Attach files to YouTrack**:
   - `geometry.png` - Geometry cross-sections
   - `fill_sweep.png` - k-eff vs fill fraction plot
   - `all_results.csv` - Combined raw data from all runs
   - Upload via YouTrack API attachments endpoint
   - Images will be referenced by filename in the comment

3. **Post FULL REPORT as YouTrack comment** with:
   - Executive summary table (key metrics + status)
   - Complete data tables for ALL steps (not just summaries)
   - Image references (YouTrack renders attached images inline)
   - Safety determination and conclusions

   **IMPORTANT:** The comment should contain the COMPLETE report so reviewers can see everything directly in YouTrack without downloading attachments. Include:
   - All k-eff values from Step 1 (geometry sweep)
   - All k-eff values from Step 2 (H/U sweep)
   - All k-eff values from Step 3 (fill sweep)
   - Worst-case geometry identification
   - Critical threshold (or "SAFE BY DESIGN" if none)
   - Safety margins

4. **Mark ticket complete:**
   ```bash
   python scripts/youtrack/youtrack_cli.py mark-complete {TICKET_ID}
   ```

**Example YouTrack comment structure:**
```markdown
## {TICKET_ID}: Analysis Complete - FINAL REPORT

### Executive Summary
| Metric | Value | Status |
|--------|-------|--------|
| UF6 k-eff (max) | X.XXX | SAFE/MARGINAL/CRITICAL |
| UO2F2 k-eff (max) | X.XXX | SAFE/MARGINAL/CRITICAL |
| Critical threshold | XX% / None | Status |

### Step 1: UF6 Dry Results (N cases)
[Full data table with all geometry cases]

### Step 2: H/U Sweep Results
[Full data table]

### Step 3: Fill Sweep Results
[Full data table]

![Fill Sweep](fill_sweep.png)
![Geometry](geometry.png)

### Conclusions
[Safety determination, key findings, recommendations]
```

---

## Directory Structure After Run

```
experiments/crit_requests/{TICKET_ID}/
├── _config/
│   ├── uf6_dry.yaml           # Geometry sweep config
│   ├── uo2f2_hu_sweep.yaml    # H/U sweep (worst-case geometry)
│   └── uo2f2_fill_sweeps/     # All fill sweep configs in one folder
│       ├── case_1.yaml        # pipe_size=3, gap=0
│       ├── case_2.yaml        # pipe_size=3, gap=10
│       └── case_N.yaml        # etc.
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
│   │       └── ...
│   └── uo2f2_fill_sweeps/     # All fill sweeps under one directory
│       └── {timestamp}/
│           ├── all_results.csv     # Combined results from all geometries
│           ├── case_1/
│           │   ├── config.yaml
│           │   ├── results.csv
│           │   └── cases/
│           ├── case_2/
│           │   └── ...
│           └── case_N/
├── results/                   # FINAL DELIVERABLE
│   ├── REPORT.md              # Generated from template
│   ├── all_results.csv
│   └── plots/
│       ├── geometry.png
│       ├── hu_sweep.png
│       └── fill_overlay.png   # All geometries on one plot
├── summary_plots/
│   ├── geometry_comparison.png
│   ├── hu_sweep.png
│   └── fill_overlay.png
└── experiment-plan.md
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
│  Step 1: UF6 Dry (Geometry Sweep)                                          │
│  ├─ Sweep: gap_cm: [5, 10, 15], pipe_size: [3, 4, 6]                       │
│  ├─ Output: k-eff for each geometry (9 cases)                              │
│  ├─ Find: WORST-CASE for H/U sweep → gap=5, pipe=6                         │
│  └─ Record: ALL geometry cases for Step 3                                  │
│                    ↓                                                       │
│  Step 2: H/U Sweep (at worst-case geometry)                                │
│  ├─ Fixed: gap_cm: 5, pipe_size: 6 (worst-case from Step 1)                │
│  ├─ Sweep: h_to_u: [0, 10, 20, 30, 40, 50]                                 │
│  ├─ Output: k-eff for each H/U                                             │
│  └─ Find: PEAK H/U → h_to_u = 20 (highest k-eff)                           │
│                    ↓                                                       │
│  Step 3: Fill Sweep (ALL geometries at peak H/U)                           │
│  ├─ For EACH geometry from Step 1:                                         │
│  │   ├─ Fixed: geometry + h_to_u: 20 (peak)                                │
│  │   └─ Sweep: fill_fraction: [0.1, 0.2, ..., 1.0]                         │
│  ├─ Output: k-eff vs fill for ALL geometries (9 curves)                    │
│  ├─ Generate: fill_overlay.png (all curves on one plot)                    │
│  └─ Find: CRITICAL THRESHOLD for each geometry                             │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

**Key Change:** Step 3 now runs fill sweep for ALL geometries (not just worst-case).
This produces an overlay plot showing fill% curves for every geometry, making it
easy to compare critical thresholds across configurations.
