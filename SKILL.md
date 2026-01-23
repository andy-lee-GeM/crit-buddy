# Crit-Buddy Assistant Skill

This skill helps engineers set up and run criticality safety parametric studies using crit-buddy.

## Overview

Crit-buddy is a criticality safety analysis framework for parametric nuclear criticality studies. It allows engineers to explore how design parameters affect nuclear criticality (k-eff values) using Monte Carlo simulation codes (OpenMC and MCNP).

## Workflow

When an engineer wants to run a criticality study, guide them through these steps:

### Step 1: Select a Problem Template

Available templates are located in `templates/`. Each template represents a different geometry configuration.

**Current templates:**
- `single_cylinder` - A vertical cylinder filled with UF6 fissile material, surrounded by a wall and reflector

To understand a template's parameters, read its schema file at `templates/{problem}/schema.yaml` and the template class in `templates/{problem}/__init__.py`.

### Step 2: Gather User Parameters

For the selected template, ask the engineer about each relevant parameter. For `single_cylinder`:

| Parameter | Description | Default | Range/Options |
|-----------|-------------|---------|---------------|
| `enrichment` | U-235 weight percent | 5.0 | 0.7-100% |
| `radius_cm` | Inner cylinder radius | **required** | positive |
| `height_cm` | Cylinder height | 100 | positive |
| `wall_material` | Container material | "aluminum" | "aluminum", "steel" |
| `wall_thickness_cm` | Wall thickness | 0.3175 | positive |
| `reflector_material` | Reflector type | - | "water", "concrete", "none" |
| `reflector_thickness_cm` | Reflector thickness | 30.0 | positive |
| `uf6_density` | UF6 density (g/cc) | 5.09 | positive |

**Important:** Ask if they want to sweep any parameters (run multiple values). Parameters with list values create a cartesian product of cases.

### Step 3: Create Experiment Configuration

Create a YAML config file at `experiments/{experiment_name}/experiment.yaml`:

```yaml
problem: single_cylinder
name: "Descriptive Experiment Name"

# Fixed parameters (single values)
enrichment: 5.0
height_cm: 100
wall_material: aluminum
wall_thickness_cm: 0.3175
reflector_material: water
reflector_thickness_cm: 30.0
uf6_density: 5.09

# Swept parameters (lists) - creates multiple cases
radius_cm: [5, 10, 15, 20]
```

### Step 4: Verify Machine Configuration

Ensure `config.yaml` exists in the project root with proper paths:

```yaml
conda_env: openmc-env
openmc_cross_sections: /path/to/cross_sections.xml
mcnp:
  executable: /path/to/mcnp6.exe
  tasks: 4
  timeout: 3600
```

### Step 5: Run the Experiment

The recommended workflow uses OpenMC for rapid iteration, then MCNP for final review-ready cases.

**Stage 1: Iterate with OpenMC (default)**

```bash
# Validate geometry first (no simulation)
python run_study.py experiments/{name}/experiment.yaml --validate

# Quick smoke test (1 case, reduced particles)
python run_study.py experiments/{name}/experiment.yaml --smoke

# Full run with OpenMC (default solver)
python run_study.py experiments/{name}/experiment.yaml

# Run specific case by label
python run_study.py experiments/{name}/experiment.yaml --case "10_water"
```

Review the OpenMC results. If the engineer is satisfied with the parameter sweep and results look reasonable, proceed to Stage 2.

**Stage 2: Generate MCNP cases for review**

Once OpenMC results are acceptable, run with MCNP to prepare cases for formal review:

```bash
# Run with MCNP to generate review-ready cases
python run_study.py experiments/{name}/experiment.yaml --solver mcnp
```

This generates MCNP input decks and results that can be reviewed and archived for compliance documentation.

### Step 6: Interpret Results

Results are written to `experiments/{name}/runs/{timestamp}/`:
- `results.csv` - All parameters and k-eff values
- `plots/` - Visualization of k-eff vs swept parameters

**Safety Classification:**
- `SAFE`: k-eff + 2σ < 0.95 (safety limit)
- `MARGINAL`: 0.95 ≤ k-eff + 2σ < 1.0
- `CRITICAL`: k-eff + 2σ ≥ 1.0

## Example Conversations

### Engineer wants to study cylinder radius effects:
1. Ask: What enrichment level? What reflector configuration?
2. Ask: What range of radii to study?
3. Create config with radius as swept parameter
4. Recommend `--validate` first, then `--smoke`, then full OpenMC run
5. Review OpenMC results together - if satisfied, run with `--solver mcnp` for review-ready cases

### Engineer wants to compare materials:
1. Identify which material parameter to vary (wall or reflector)
2. Create config with material as swept parameter
3. Note that string parameters can also be swept: `wall_material: [aluminum, steel]`
4. Run OpenMC first, then MCNP once parameters are finalized

### Engineer ready for formal review:
1. Confirm OpenMC results look reasonable
2. Run with `--solver mcnp` to generate MCNP input decks
3. Point them to `experiments/{name}/runs/latest/cases/` for MCNP files
4. Results CSV includes both OpenMC and MCNP k-eff values for comparison

### Engineer debugging a failed run:
1. Check `config.yaml` for correct paths
2. Check solver availability
3. Review case output in `experiments/{name}/runs/latest/cases/{case}/{solver}/`

## Key Files Reference

- `run_study.py` - Main entry point
- `config.yaml` - Machine-specific paths (not in git)
- `templates/{problem}/schema.yaml` - Parameter definitions
- `templates/{problem}/__init__.py` - Template class with `derive_params()`
- `critbuddy/core/materials.py` - Shared material definitions
- `critbuddy/solvers/` - OpenMC and MCNP solver implementations
