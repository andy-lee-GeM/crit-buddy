# Crit-Buddy

Parametric nuclear criticality safety analysis using OpenMC.

## Quick Start

```bash
# Run a study
python run_study.py path/to/config.yaml

# Run with MCNP instead of OpenMC
python run_study.py path/to/config.yaml --solver mcnp
```

## Config File Format

```yaml
problem: cylinder          # Template: cylinder, pipe, rectangular_box, shipping_cylinder
name: "My Analysis"        # Human-readable name

# Required parameters (vary by template)
enrichment: 20             # wt% U-235
radius_cm: 7.62            # Cylinder radius
height_cm: 100             # Cylinder height

# Sweep parameters (use lists)
gap_cm: [0, 5, 10, 15]     # Creates 4 cases
rows: [1, 2, 3]            # Combined with above = 12 cases

# Optional
wall_material: steel               # steel, aluminum, ss304, monel
environment_material: humid_air    # humid_air, air, water
environment_density: 0.0011        # g/cc
reflector_thickness_cm: 30
```

## Available Templates

| Template | Description | Key Parameters |
|----------|-------------|----------------|
| `cylinder` | Vertical cylinder or 3D array | radius_cm, height_cm, rows, cols, layers, gap_cm |
| `pipe` | Horizontal pipe or 2D array | pipe_size, length_cm, rows, cols, gap_cm |
| `rectangular_box` | Box geometry | length_cm, width_cm, height_cm |
| `shipping_cylinder` | ANSI N14.1 cylinders | cylinder_type (30B, 48Y, etc.) |

## Output

Results are saved to:
```
experiments/crit_requests/{name}/
└── runs/{config_name}/    # Simulation results
    └── {timestamp}/
        ├── results.csv    # k-eff values
        └── cases/         # Per-case outputs
```

## Examples

```bash
# Single cylinder at 20% enrichment
python run_study.py experiments/crit_requests/CB-7/_config/uf6_dry.yaml

# Run with both solvers (if MCNP is installed)
python run_study.py experiments/crit_requests/CB-7/_config/uf6_dry.yaml --solver all
```

## Requirements

- Python 3.9+
- OpenMC with Python bindings
- Nuclear data library (ENDF/B-VII.1 or similar)

## Setup

### 1. Install OpenMC

Follow the [OpenMC installation guide](https://docs.openmc.org/en/stable/usersguide/install.html) or use conda:

```bash
conda create -n openmc-env python=3.11
conda activate openmc-env
conda install -c conda-forge openmc
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Download nuclear data

```bash
# Download ENDF/B-VII.1 cross-sections (~1.5 GB)
python -c "import openmc.data; openmc.data.download_nndc_data('endfb71')"
```

### 4. Create config.yaml

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your paths:

```yaml
# Conda environment name
conda_env: openmc-env

# Path to cross-sections XML
openmc_cross_sections: /path/to/cross_sections.xml

# Optional: MCNP configuration
mcnp:
  executable: /path/to/mcnp6
  tasks: 4
  timeout: 3600
```

### 5. Verify installation

```bash
python run_study.py --help
```
