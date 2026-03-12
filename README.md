# Crit-Buddy

Parametric nuclear criticality safety analysis using OpenMC.

## Quick Start

```bash
# Run a study
python run_study.py path/to/config.yaml

# Run with MCNP instead of OpenMC
python run_study.py path/to/config.yaml --solver mcnp

# Skip plot/report generation
python run_study.py path/to/config.yaml --no-report
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
wall_material: steel               # steel, aluminum, ss304
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
python run_study.py experiments/crit_requests/CB-7/_config/01_uf6_dry.yaml

# Run with both solvers (if MCNP is installed)
python run_study.py experiments/crit_requests/CB-7/_config/01_uf6_dry.yaml --solver all
```

## Requirements

- Python 3.9+
- OpenMC with Python bindings
- Nuclear data library (ENDF/B-VII.1 or similar)

## Material Models

`UO2F2` density is derived from the ORNL report `ORNL/TM-12292`, Appendix A.
The implementation in [`critbuddy/core/uo2f2_physics.py`](/home/gem/Projects/crit-buddy/critbuddy/core/uo2f2_physics.py) uses the uranium-density relationship from Eq. (A.1), plus the uranyl-fluoride-specific low-H/U hydrated-salt branch used below `H/U = 4`, and then converts that uranium density into bulk mixture density from the requested `H/U` and enrichment.

The model constants are centralized in `ATOMIC_MASSES` and `UO2F2_MODEL` so the molar masses, molar volumes, hydration terms, and branch coefficients are kept in one place.

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
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -m pip install -r requirements.txt
```

### 3. Provision nuclear data

If you are setting up another development environment, reuse an existing OpenMC HDF5
library instead of downloading it again when possible. See
[`docs/openmc-data-setup.md`](docs/openmc-data-setup.md) for the internal setup flow
used with this repo.

```bash
# Download/extract ENDF/B-VII.1 HDF5 data (~1.6 GB compressed)
mkdir -p ~/openmc_data
cd ~/openmc_data
wget -O endfb-vii.1-hdf5.tar.xz https://anl.box.com/shared/static/9igk353zpy8fn9ttvtrqgzvw1vtejoz6.xz
tar -xJf endfb-vii.1-hdf5.tar.xz
```

### 4. Create config.yaml

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your paths:

```yaml
# Conda environment name
conda_env: openmc-env

# Path to cross_sections.xml
openmc_cross_sections: /path/to/cross_sections.xml

# Optional: MCNP configuration
mcnp:
  executable: /path/to/mcnp6
  tasks: 4
  timeout: 3600
```

`run_study.py` will export `OPENMC_CROSS_SECTIONS` from `config.yaml` if the file
exists and the environment variable is not already set.

### 5. Verify installation

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -c "import openmc, yaml; print(openmc.__version__); from pathlib import Path; cfg = yaml.safe_load(open('config.yaml')); p = Path(cfg['openmc_cross_sections']); print(p); print(p.exists())"
```

### 6. Cascade Array Manual Check

```bash
# Geometry/visualization manual regression coverage
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -m unittest tests.test_cascade_array_model
```
