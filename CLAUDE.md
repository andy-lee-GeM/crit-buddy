# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Crit-Buddy** is a nuclear criticality safety analysis tool. It answers: *"Will this geometry go critical?"*

**What it does:**
1. Takes geometry descriptions (pipe arrays, cylinder arrays, shipping containers)
2. Runs Monte Carlo simulations (OpenMC/MCNP) to calculate k-eff
3. Generates reports with safety thresholds for engineers

**Standard 3-Step Safety Case:**
```
Step 1: UF6 Dry (Geometry Sweep)
→ Find worst-case geometry, confirm subcritical for dry UF6

Step 2: H/U Sweep (at worst-case geometry)
→ Find peak moderation (optimal H/U ratio)

Step 3: Fill Sweep (at worst-case + peak H/U)
→ Find critical threshold (fill % where k+2σ ≥ 0.95)
```

**Output:** Reports telling engineers:
- UF6 max k-eff (geometry safety margin)
- UO2F2 critical threshold (fill % limit for wet conditions)

**Workflow:** See `.claude/skills/run-cb-daily/SKILL.md` (Standard Workflow section)

**Report Template:** See `docs/templates/cb-final-report-template.md`

## Current Work

Active tickets are in `experiments/crit_requests/CB-*/`

## Criticality Safety Approach

### Conservative Assumptions

All analyses use bounding (conservative) assumptions:

1. **Optimal Moderation**: Water density set to peak reactivity (~0.5 g/cc)
   - Bounds mist/water ingress scenarios
   - Determined by moderation sweep experiments

2. **Full Reflection**: 30 cm water reflection on all sides

3. **Maximum Fill**: 100% fill fraction

4. **Pure UF6**: Model fissile material as pure UF6 at solid density (5.09 g/cc)
   - This bounds actual chemistry (NaF complexes, Al2O3 beds) which would reduce reactivity

5. **Maximum Credible Enrichment**: Each analysis uses the highest credible enrichment for the scenario

### Material Modeling

**Material Functions** (`critbuddy/core/materials.py`):
- `create_uf6(enrichment, density)` - Pure UF6 (primary)
- `create_uf6_with_hf(enrichment, density)` - UF6 + HF for 30B cylinders
- Registry materials: `aluminum()`, `stainless_steel_316()`, `water()`, etc.
- MCNP equivalents: `mcnp_uf6()`, `mcnp_aluminum()`, etc.

### Experiment Directory Structure

Each experiment follows this standard structure (ticket ID format: `CRIT-NNN`):

```
CRIT-001/
├── _config/                    # Input YAML configs
│   ├── uf6_dry.yaml
│   ├── uo2f2_hu_sweep.yaml
│   └── uo2f2_fill_sweep.yaml
├── _validation/                # Geometry validation (from --validate)
│   ├── geometry.png
│   └── voxel_3d.png
├── runs/                       # Raw run outputs (auto-generated)
│   ├── uf6_dry/
│   │   └── {timestamp}/
│   │       ├── config.yaml
│   │       ├── results.csv
│   │       └── cases/
│   └── uo2f2_hu_sweep/
├── results/                    # Final deliverables
│   ├── plots/
│   ├── RESULTS_SUMMARY.md
│   └── CALCULATION_REPORT.docx
└── EXPERIMENT_PLAN.md          # Required: defines scope and methodology
```

**Key directories:**
- `_config/` — Input YAML configs (config name → run folder name)
- `_validation/` — Geometry checks before running
- `runs/` — Raw outputs from each config run
- `results/` — Final plots, tables, and reports

### Experiment Planning

**Always create `EXPERIMENT_PLAN.md` before running.** See `08_pipe_array_3d/experiment-plan.md` as a template.

The plan must include:

1. **Objective** — What question are we answering?
2. **Configuration Summary** — Table of parameters and values
3. **Scenarios** — List of configs with purpose and case counts
4. **Sweep Matrix** — Detailed case breakdown per scenario
5. **Phases** — Setup → Validate → Run → Analyze workflow
6. **Success Criteria** — How do we know we're done?

Example scenario naming:
- `uf6_air.yaml` — UF6 with air environment
- `uf6_water.yaml` — UF6 with water reflection
- `uo2f2_dry_air.yaml` — Dry UO2F2 with air
- `uo2f2_wet_water.yaml` — Wet UO2F2 with water reflection
- `uo2f2_hu_sweep.yaml` — H/U ratio sweep to find peak

### Output Interpretation

**1-D Sweeps**: Line graphs + tables (k-eff vs parameter)
**2-D Sweeps**: Heatmaps with safe/critical boundary contours

**Status Classification:**
- SAFE: k-eff + 2σ < 0.95
- MARGINAL: 0.95 ≤ k-eff + 2σ < 1.0
- CRITICAL: k-eff + 2σ ≥ 1.0

## Common Commands

```bash
# Run an experiment
/home/gem/.local/miniforge3/envs/openmc-env/bin/python run_study.py experiments/crit_requests/01_single_cylinder/enr_20/radius_height.yaml

# Run without generating plots/report
/home/gem/.local/miniforge3/envs/openmc-env/bin/python run_study.py experiments/crit_requests/01_single_cylinder/enr_20/radius_height.yaml --no-report

# Cascade-array manual visualization regression check
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -m unittest tests.test_cascade_array_model

# Use specific solver (openmc, mcnp, or all)
/home/gem/.local/miniforge3/envs/openmc-env/bin/python run_study.py experiments/crit_requests/02_process_pipe/enr_24/nps_sweep.yaml --solver openmc
```

## YouTrack Integration

Unified client for ticket management. Requires `YOUTRACK_TOKEN` env var and `youtrack` config in `config.yaml`.

### CLI Commands

```bash
# Fetch tickets
python -m critbuddy.integrations.youtrack.cli fetch-ready              # All Ready-for-run tickets
python -m critbuddy.integrations.youtrack.cli fetch CB-10              # Single ticket
python -m critbuddy.integrations.youtrack.cli fetch CB-10 --json       # JSON output

# Push results to ticket
python -m critbuddy.integrations.youtrack.cli push-results CB-10 experiments/crit_requests/CB-10/results

# Update ticket status
python -m critbuddy.integrations.youtrack.cli update-status CB-10 "In Progress"
python -m critbuddy.integrations.youtrack.cli mark-complete CB-10
python -m critbuddy.integrations.youtrack.cli mark-failed CB-10 "Error message"

# Add comment
python -m critbuddy.integrations.youtrack.cli comment CB-10 "Analysis started"

# Template forms
python -m critbuddy.integrations.youtrack.cli list-forms
python -m critbuddy.integrations.youtrack.cli create-form pipe
```

### Python API

```python
from critbuddy.integrations.youtrack import YouTrackClient

client = YouTrackClient()

# Read operations
tickets = client.get_ready_tickets()
ticket = client.get_ticket("CB-10")

# Update operations
client.mark_in_progress("CB-10")
client.add_comment("CB-10", "Analysis started")
client.attach_file("CB-10", Path("results/plot.png"))
client.mark_complete("CB-10")

# Push full results (CSV, plots, report as comment)
client.push_results("CB-10", Path("experiments/CB-10/results"))
```

## Architecture

### Entry Points
- `run_study.py` - CLI entry point, delegates to `critbuddy.runner.main()`

### Core Package (`critbuddy/`)

**Configuration (`core/config.py`):**
- `ExperimentConfig` - Loads YAML experiment files
- `Case` - Single simulation with resolved parameters
- `expand_sweeps()` - Converts list parameters to cartesian product of cases
- `generate_cases()` - Creates Case objects with defaults and derived parameters

**Materials (`core/materials.py`):**
- `create_uf6(enrichment, density)` - Pure UF6 (primary)
- `create_uf6_with_hf(enrichment, density)` - UF6 + HF for 30B cylinders
- Registry materials: `aluminum()`, `stainless_steel_316()`, `water()`, etc.
- MCNP equivalents: `mcnp_uf6()`, `mcnp_aluminum()`, etc.

**Solvers (`solvers/`):**
- `Solver` (base class) - Abstract interface with `run()` and `validate()` methods
- `SolverResult` - Dataclass with `keff`, `uncertainty`, `status`, `k2sigma` property
- `OpenMCSolver` - Builds OpenMC model, runs simulation, parses statepoint
- `MCNPSolver` - Generates MCNP input, executes, parses output

**Template Base (`core/template.py`):**
- `ProblemTemplate` - Base class for geometry templates
- `ParameterSpec` - Parameter schema (type, required, default, min/max, unit)
- Each template defines `PARAMETERS`, `SIMULATION` (particle/batch counts), `SAFETY_LIMIT`
- Abstract method: `derive_params(user_params)` - calculates derived geometry values

### Template Directory (`templates/`)

Each template has:
- `__init__.py` - Exports `Template` class inheriting from `ProblemTemplate`
- `openmc/model.py` - `build_model(params)` returns `(materials, geometry, dims)`
- `mcnp/model.py` - Optional MCNP implementation

**Available templates:**

| Template | Description | Use Case |
|----------|-------------|----------|
| `cylinder` | Single or 3D array of vertical cylinders | Traps, vessels, pumps, storage arrays |
| `pipe` | Single or 2D array of horizontal pipes | Process piping, cascade lines |
| `rectangular_box` | Rectangular parallelepiped | HEPA filters, chemical traps |
| `shipping_cylinder` | Single ANSI N14.1 cylinder | Shipping/storage containers (30B, 48Y, etc.) |
| `cascade_array` | Hierarchical cylinder array | Cascade enrichment plants |

### Template Quick Reference

#### `cylinder`

Single or 3D array of vertical cylinders (rows × cols × layers).

```yaml
problem: cylinder
name: "Cylinder Array Analysis"
enrichment: 21              # wt% U-235 [REQUIRED]

# Array (defaults to single cylinder)
rows: 3                     # 1-150 (default: 1)
cols: 4                     # 1-10 (default: 1)
layers: 2                   # 1-10 (default: 1)
gap_horizontal_cm: 12.7     # Horizontal gap between cylinder walls
gap_vertical_cm: 7.62       # Vertical gap between layers
# OR use gap_cm for uniform spacing in all directions

# Cylinder geometry
radius_cm: 12.7             # Inner radius [REQUIRED]
height_cm: 100              # Cylinder height [REQUIRED]
wall_material: steel        # steel, aluminum, ss304
wall_thickness_cm: 0.6      # Wall thickness

# Environment
environment: humid_air      # humid_air, air, water
reflector_thickness_cm: 30  # 0-100 cm
```

#### `pipe`

Single or 2D array of horizontal pipes (rows × cols).

```yaml
problem: pipe
name: "Pipe Array Analysis"
enrichment: 21              # wt% U-235 [REQUIRED]

# Array (defaults to single pipe)
rows: 2                     # 1-10 (default: 1) - vertical stacking
cols: 3                     # 1-10 (default: 1) - side by side
gap_cm: 5.0                 # 0-100 cm (default: 5.0)

# Pipe geometry
pipe_size: "2"              # NPS: 1/8, 1/4, ..., 8, or "custom"
length_cm: 100              # 1-1000 cm [REQUIRED]

# Environment
wall_material: ss304        # ss304, steel, aluminum
environment: humid_air      # humid_air, air, water
reflector_thickness_cm: 30  # 0-100 cm
```

#### `shipping_cylinder`

Single ANSI N14.1 cylinder with dimensions from registry.

```yaml
problem: shipping_cylinder
name: "30B Cylinder Analysis"
enrichment: 5               # wt% U-235 [REQUIRED]
cylinder_type: 30B          # 5A, 5B, 30B, 48X, 48Y, 48G, 48O [REQUIRED]

# Environment
environment: water          # water, air, none
reflector_thickness_cm: 30  # 0-100 cm
```

#### Standard Safety Case Configs

For any template, the standard 3-step analysis uses:

```yaml
# uf6_dry.yaml - Step 1
fissile_material: uf6
fissile_density: 5.09
fill_fraction: 1.0

# uo2f2_hu_sweep.yaml - Step 2
fissile_material: uo2f2
fissile_density: 6.37
fill_fraction: 1.0
h_to_u: [0, 10, 20, 30, 50]

# uo2f2_fill_sweep.yaml - Step 3
fissile_material: uo2f2
fissile_density: 6.37
h_to_u: {peak from step 2}
fill_fraction: [0.1, 0.25, 0.5, 0.75, 1.0]
```

### Experiments Directory

```
experiments/
├── benchmarks/           # Validation against published results
│   └── uf6_30b/          # ORNL 30B cylinder benchmarks
└── crit_requests/        # Current criticality analysis requests
    ├── CRIT-001/             # Ticket-based naming
    ├── CRIT-002/
    └── _archive/             # Old numbered experiments (reference)
```

### Experiment YAML Format

```yaml
problem: cylinder                 # Template name (required)
name: "My Analysis"               # Human-readable name
enrichment: 20.0                  # Fixed parameter
radius_cm: [10, 15, 20, 25, 30]   # Swept parameter (creates 5 cases)
height_cm: [50, 100, 150, 200]    # Another sweep (creates 5×4 = 20 cases)
environment: water                # Environment/reflector material
fissile_density: 5.09             # Fissile material density (g/cc)
```

Lists in parameters trigger cartesian product expansion into multiple cases.

## Configuration

Create `config.yaml` (not in git) with local paths:

```yaml
conda_env: openmc-env
openmc_cross_sections: /path/to/cross_sections.xml
mcnp:
  executable: /path/to/mcnp6.exe
  tasks: 4
  timeout: 3600
```

## Output Structure

```
experiment_dir/
├── runs/{run_name}/{timestamp}/
│   ├── config.yaml          # Copy of experiment YAML
│   ├── results.csv          # k-eff values for all cases
│   ├── plots/               # k-eff vs parameter plots
│   ├── cases/{case}/        # Per-case solver outputs
│   └── consultant_package/  # Verification package (with --package)
└── runs/{run_name}/latest -> {timestamp}
```

## Key Concepts

**Parameter Flow:**
1. User params from YAML → lowercase (e.g., `radius_cm`)
2. Template `derive_params()` → derived params uppercase (e.g., `R1`, `R2`, `ENRICHMENT`)
3. All merged into single `params` dict passed to solver

**Dynamic Loading:**
- Templates loaded via `importlib.util` from `templates/{name}/__init__.py`
- Solver model modules loaded from `templates/{name}/{solver}/model.py`

## Skills

Skills are reusable workflows for common tasks. Invoke with `/skill-name`.

### `/calculation-report` - Generate Formal Calculation Report

Transforms experiment results into a formal Safe-by-Design calculation document.

**Usage:**
```
/calculation-report [experiment_directory]
```

**What it does:**
1. Gathers data from `runs/*/results.csv` and `EXPERIMENT_PLAN.md`
2. Generates structured markdown report demonstrating safe-by-design:
   - Executive Summary with key finding and margins table
   - Critical threshold analysis (fill fraction where k-eff becomes critical)
   - Accumulation analysis (max credible fissile buildup)
   - Safety margin calculation (threshold / accumulation)
3. Creates briefing slide outline for PPTX generation
4. Converts to formatted Word document (.docx)

**Report sections:**
- **Executive Summary**: Key finding, margins table, conclusion
- **Section 6 (Results)**: k-eff vs fill fraction, critical thresholds
- **Section 7 (Accumulation)**: Mechanism, inputs, calculation
- **Section 8 (Safety Margin)**: Critical threshold vs max accumulation
- **Appendices**: Geometry, density calcs, accumulation derivation, raw data

**Key terminology:**
- **Safe-by-Design**: Critical threshold >> max accumulation (no controls needed)
- **Critical Threshold**: Fill fraction or mass where k-eff + 2σ ≥ 0.95
- **Safety Margin**: Expressed as "X×" multiplier (e.g., "8.6×")
- SAFE/MARGINAL/CRITICAL status based on k-eff + 2σ

**Output files:**
- `results/{NAME}_CALCULATION.md` - Full calculation report
- `results/{NAME}_CALCULATION.docx` - Formatted Word document
- `results/{NAME}_BRIEFING.md` - Slide outline for PPTX
- `results/plots/` - Generated visualizations

### `/review-experiment` - Review Experiment Before Running

Comprehensive review checklist for validating experiment configuration before approval.

**Usage:**
```
/review-experiment [experiment_path]
```
