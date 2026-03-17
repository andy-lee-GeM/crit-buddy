# Crit-Buddy

OpenMC-based nuclear criticality analysis for reusable models, formal studies,
and ticket-driven requests. MCNP decks are kept as manual reference artifacts
inside model folders when needed.

## Project Layout

```text
models/     canonical physical systems
studies/    formal analysis and validation work
requests/   ticket-driven operational analyses
workbench/  exploratory or archived engineering work
critbuddy/  shared execution and reporting code
docs/       shared setup and reference docs
tests/      model and physics tests
```

The preferred workflow is:

1. Define a canonical model under `models/`.
2. Run OpenMC studies from `studies/` or `requests/`.
3. Keep generated runs outside the model directory.
4. Keep manual MCNP decks under `models/<name>/mcnp/`.

## Running Studies

```bash
# Run a study
python run_study.py studies/centrifuge-unit-cell-fill-sweep/study.yaml

# Run a request config
python run_study.py requests/CB-11/configs/01_uf6_dry.yaml

# Skip plot/report generation
python run_study.py studies/centrifuge-unit-cell-fill-sweep/study.yaml --no-report
```

## Config Format

Model-based configs are the preferred format:

```yaml
model: centrifuge-unit-cell
name: "Centrifuge Unit Cell Fill Sweep"

params:
  fill_z_cm: [10, 20, 30, 40, 50]
  source_z_cm: 10
  x_boundary_type: reflective
  y_boundary_type: reflective
  z_boundary_type: reflective
```

Legacy template-based configs are still supported for existing request and
benchmark work:

```yaml
problem: shipping_cylinder
name: "ORNL 30B Single Cylinder Sweep"

enrichment: [6, 7, 8, 9, 10, 12, 15, 20]
uf6_density: [2.5, 3.5, 4.5, 5.5]
```

## Model Documentation

Each canonical model should include a `MODEL.md` file with this structure:

- `Overview`
- `Files`
- `Geometry Summary`
- `Modeling Assumptions`
- `Validation`
- `History`

This is the stable model handoff document for the team. Detailed validation
results and solver comparisons belong under `studies/`.

## Outputs

Results are written beside the config that was run:

```text
<study-or-request>/
└── runs/{config_name}/
    └── {timestamp}/
        ├── config.yaml
        ├── results.csv
        └── cases/
```

Study-specific reports or merged solver comparisons can live at the study root,
for example:

```text
studies/centrifuge-unit-cell-parity/
  study.yaml
  report.md
  results.csv
  openmc/
  mcnp/
```

## Materials and Physics

`UO2F2` density and composition logic live under `critbuddy/core/materials/`.
The current implementation follows the project's hydrated uranyl fluoride model
and is covered by the dedicated physics tests.

## Setup

### 1. Install OpenMC

Use your normal Python environment tooling. One common approach is conda:

```bash
conda create -n openmc-env python=3.11
conda activate openmc-env
conda install -c conda-forge openmc
python -m pip install -r requirements.txt
```

### Codex Environment

In the Codex execution environment used for repo work, OpenMC is installed and
available from:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python
```

Future coding sessions should use that interpreter for any OpenMC-backed import,
script, or test instead of assuming `openmc` is unavailable on the path.

Examples:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -c "import openmc; print(openmc.__version__)"
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -m unittest tests.unit.materials.test_builders tests.unit.materials.test_properties tests.unit.materials.test_uo2f2_physics
/home/gem/.local/miniforge3/envs/openmc-env/bin/python scripts/get_mcnp_density.py water
```

That path is specific to this Codex environment and should not be assumed to
match a developer's local machine.

### 2. Configure Nuclear Data

Create `config.yaml` from the example:

```bash
cp config.yaml.example config.yaml
```

Set:

```yaml
conda_env: openmc-env
openmc_cross_sections: /path/to/cross_sections.xml
```

See `docs/openmc-data-setup.md` for the full data setup flow.

### 3. Verify

```bash
python -c "import openmc, yaml; print(openmc.__version__); from pathlib import Path; cfg = yaml.safe_load(open('config.yaml')); p = Path(cfg['openmc_cross_sections']); print(p); print(p.exists())"
```

## Tests

The lean test suite covers:

- canonical model construction
- shared material and geometry unit coverage
- `UO2F2` physics utilities

Example:

```bash
python -m unittest tests.integration.models.test_centrifuge_unit_cell tests.unit.materials.test_builders tests.unit.materials.test_uo2f2_physics
```

In the Codex environment, use:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -m unittest tests.unit.materials.test_builders tests.unit.materials.test_properties tests.unit.materials.test_uo2f2_physics tests.unit.geometry.test_cylinders tests.unit.geometry.test_pipes tests.integration.models.test_cylinder_unit_cell tests.integration.models.test_cascade_array tests.integration.models.test_centrifuge_unit_cell
```
