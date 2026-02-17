# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Crit-Buddy is a parametric nuclear criticality safety analysis framework using Monte Carlo codes (OpenMC and MCNP). It automates parametric criticality studies by sweeping user-defined parameters, running simulations with multiple solvers, and generating verification packages for independent review.

## Current Work

See `experiments/crit_requests/PLAN.md` for the current experiment execution plan and status.

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
- Registry materials: `create_aluminum()`, `create_steel()`, `create_water()`, etc.
- MCNP equivalents: `mcnp_uf6()`, `mcnp_aluminum()`, etc.

### Experiment Structure

Experiments organized by enrichment level:
- `enr_05/` - 5% (LEU limit)
- `enr_10/` - 10%
- `enr_15/` - 15% (HALEU)
- `enr_20/` - 20% (HALEU)
- `enr_24/` - 24% (HALEU max for these studies)

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
/home/andylee/anaconda3/envs/openmc-env/bin/python run_study.py experiments/crit_requests/01_single_cylinder/enr_20/radius_height.yaml

# Quick smoke test (1 case, minimal particles)
/home/andylee/anaconda3/envs/openmc-env/bin/python run_study.py experiments/crit_requests/01_single_cylinder/enr_20/radius_height.yaml --smoke

# Validate geometry (generates 2D plots in _validation/)
/home/andylee/anaconda3/envs/openmc-env/bin/python run_study.py experiments/crit_requests/01_single_cylinder/enr_20/radius_height.yaml --validate

# Run specific case only
/home/andylee/anaconda3/envs/openmc-env/bin/python run_study.py experiments/crit_requests/01_single_cylinder/enr_20/radius_height.yaml --case "R=25cm"

# Use specific solver (openmc, mcnp, or all)
/home/andylee/anaconda3/envs/openmc-env/bin/python run_study.py experiments/crit_requests/02_process_pipe/enr_24/nps_sweep.yaml --solver openmc
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
- Registry materials: `create_aluminum()`, `create_steel()`, `create_water()`, etc.
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

*Generic (user-specified dimensions):*
- `cylinder` - Vertical cylinder (traps, vessels, pumps)
- `cylinder_array` - Rectangular array of vertical cylinders
- `process_pipe` - Single horizontal pipe
- `parallel_pipes` - 1-3 parallel horizontal pipes
- `rectangular_box` - Rectangular parallelepiped (HEPA filters, chemical traps)

*Shipping cylinders (dimensions from ANSI N14.1 registry):*
- `shipping_cylinder` - Single shipping cylinder (30B, 48Y, 5A, 5B, etc.)
- `shipping_cylinder_array` - 3D array of stacked shipping cylinders
- `shipping_cylinder_stacked` - Horizontal shipping cylinders in pyramid/rectangular stacks

### Experiments Directory

```
experiments/
├── benchmarks/           # Validation against published results
│   └── uf6_30b/          # ORNL 30B cylinder benchmarks
└── crit_requests/        # Current criticality analysis requests
    ├── PLAN.md           # Execution plan and status
    ├── 01_single_cylinder/   # Traps, vessels, pumps
    ├── 02_process_pipe/      # Single pipes
    ├── 03_parallel_pipes/    # Cascade lines
    ├── 04_cylinder_array/    # Trap arrays
    ├── 05_shipping_cylinder/ # 30B, 48Y cylinders
    └── 06_cylinder_array_3d/ # 3D cylinder arrays
```

### Experiment YAML Format

```yaml
problem: cylinder                 # Template name (required)
name: "My Analysis"               # Human-readable name
enrichment: 20.0                  # Fixed parameter
radius_cm: [10, 15, 20, 25, 30]   # Swept parameter (creates 5 cases)
height_cm: [50, 100, 150, 200]    # Another sweep (creates 5×4 = 20 cases)
reflector_material: water         # Fixed reflector
uf6_density: 5.09                 # UF6 density (g/cc)
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

Transforms experiment results into a formal calculation document following the standard template structure.

**Usage:**
```
/calculation-report
```

**What it does:**
1. Finds completed experiment runs with `results.csv`
2. Generates structured markdown report with:
   - References, Purpose, Inputs, Assumptions, Methods, Results, Conclusions
   - Geometry visualization
   - k-eff tables and heatmaps
   - Line plots (k-eff vs parameter by enrichment)
3. Converts to formatted Word document (.docx)

**Report sections:**
- **Section 2 (Purpose)**: Narrative explaining what question the analysis answers
- **Section 3 (Inputs)**: Geometry image, configuration tables, parameter ranges
- **Section 6 (Results)**: Tables + plots for each condition (worst-case moderation, flooded)
- **Section 7 (Conclusions)**: Minimum safe values table, key findings

**Key terminology used:**
- "Worst-Case Moderation" (0.5 g/cc) - not "optimal moderation"
- Water as both "moderator" (between units) and "reflector" (surrounding array)
- SAFE/MARGINAL/CRITICAL status based on k-eff + 2σ

**Output files:**
- `{EXPERIMENT}_CALCULATION.md` - Markdown report
- `{EXPERIMENT}_CALCULATION.docx` - Formatted Word document
- `plots/` - Generated visualizations

### `/review-experiment` - Review Experiment Before Running

Comprehensive review checklist for validating experiment configuration before approval.

**Usage:**
```
/review-experiment [experiment_path]
```
