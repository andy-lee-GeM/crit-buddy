# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Crit-Buddy is a parametric nuclear criticality safety analysis framework using Monte Carlo codes (OpenMC and MCNP). It automates parametric criticality studies by sweeping user-defined parameters, running simulations with multiple solvers, and generating verification packages for independent review.

## Common Commands

**Note:** Run python with full absolute paths (e.g., `/home/user/miniconda3/envs/openmc-env/bin/python`).

```bash
# Run an experiment
python run_study.py experiments/cascade_lines/haleu.yaml

# Quick smoke test (1 case, minimal particles)
python run_study.py experiments/smoke_test/experiment.yaml --smoke

# Validate geometry (generates 2D plots in _validation/)
python run_study.py experiments/cascade_lines/haleu.yaml --validate

# Generate 3D voxel visualization
python run_study.py experiments/cascade_lines/haleu.yaml --voxel

# Run specific case only
python run_study.py experiments/cascade_lines/haleu.yaml --case "R=5cm"

# Use specific solver (openmc, mcnp, or all)
python run_study.py experiments/cascade_lines/haleu.yaml --solver mcnp

# Generate consultant verification package
python run_study.py experiments/cascade_lines/haleu.yaml --package

# Custom run name
python run_study.py experiments/cascade_lines/haleu.yaml --name my_custom_run
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
- Provides material definitions for both OpenMC and MCNP
- `create_uf6(enrichment_pct, density)`, `create_aluminum()`, `create_steel()`, `create_water()`, etc.
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

Available templates: `single_cylinder`, `cylinder_array`, `uf6_30b`

### Experiments Directory

```
experiments/
├── benchmarks/           # Validation against published results
│   └── uf6_30b/          # ORNL 30B cylinder benchmarks
├── cascade_lines/        # Single pipe studies
├── cylinder_arrays/      # Array interaction studies
├── pigtail_pipes/        # Small diameter pipes
└── smoke_test/           # Quick validation test
```

- **benchmarks/**: Cases validating against published experimental/computational results
- **other directories**: Engineering analyses and parameter sweeps

### Experiment YAML Format

```yaml
problem: single_cylinder          # Template name (required)
name: "My Analysis"               # Human-readable name
enrichment: 20.0                  # Fixed parameter
radius_cm: [1, 2, 3]              # Swept parameter (creates 3 cases)
reflector_material: [air, water]  # Another sweep (creates 2×3 cases)
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

**Status Classification (`compute_status()`):**
- SAFE: k-eff + 2σ < 0.95 (safety limit)
- MARGINAL: 0.95 ≤ k-eff + 2σ < 1.0
- CRITICAL: k-eff + 2σ ≥ 1.0

**Parameter Flow:**
1. User params from YAML → lowercase (e.g., `radius_cm`)
2. Template `derive_params()` → derived params uppercase (e.g., `R1`, `R2`)
3. All merged into single `params` dict passed to solver

**Dynamic Loading:**
- Templates loaded via `importlib.util` from `templates/{name}/__init__.py`
- Solver model modules loaded from `templates/{name}/{solver}/model.py`
