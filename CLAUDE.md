# CLAUDE.md

Repository guidance for coding agents working in Crit-Buddy.

## Current Architecture

```text
models/     canonical physical systems
studies/    formal analysis and validation work
requests/   ticket-driven operational analyses
workbench/  exploratory or archived engineering work
critbuddy/  shared execution and reporting code
docs/       shared setup and reference docs
tests/      model and physics tests
```

The active execution path is OpenMC-only. Config-driven runs do not support
MCNP. MCNP decks are stored manually under model folders as reference inputs.

## Model Conventions

- Each canonical model lives under `models/<name>/`.
- Each model should include `MODEL.md` as the handoff document.
- OpenMC implementations live under `models/<name>/openmc/`.
- Manual MCNP reference decks live under `models/<name>/mcnp/`.

## Run Conventions

- `studies/` are reusable technical analyses.
- `requests/` are ticket-backed operational analyses.
- `workbench/` is for scratch or archived work.
- New work should not go into `experiments/`.

Generated outputs should stay under the study or request that launched them:

```text
<study-or-request>/
  study.yaml or configs/*.yaml
  runs/
```

## Config Conventions

Preferred model-based config:

```yaml
model: centrifuge-unit-cell
name: Example Sweep

params:
  inner_radius_cm: 11.70
  water_film_thickness_cm: 1.0
  wall_thickness_cm: 0.3175
  fill_height_cm: [10, 20, 30]
  source_z_cm: 10
```

Legacy template-based configs still exist for older studies and requests:

```yaml
problem: shipping_cylinder
name: ORNL benchmark
```

## Testing Expectations

The maintained test suite is intentionally small:

- one test per model
- shared material and geometry unit tests
- `UO2F2` physics tests

Model-local visualization artifacts should not be committed as documentation.
If geometry construction matters, cover it in tests or a study report.

## Codex Environment

OpenMC is installed in the Codex repo-work environment. Do not assume
`ModuleNotFoundError: openmc` means OpenMC is unavailable before checking the
dedicated interpreter:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python
```

Use that interpreter for OpenMC-backed commands in this environment, for
example:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -c "import openmc; print(openmc.__version__)"
/home/gem/.local/miniforge3/envs/openmc-env/bin/python -m unittest tests.unit.materials.test_builders tests.unit.materials.test_properties tests.unit.materials.test_uo2f2_physics tests.unit.geometry.test_cylinders tests.unit.geometry.test_pipes tests.integration.models.test_cylinder_unit_cell tests.integration.models.test_cascade_array tests.integration.models.test_centrifuge_unit_cell
/home/gem/.local/miniforge3/envs/openmc-env/bin/python scripts/get_mcnp_density.py water
```

If a plain `python` or `python3` command cannot import OpenMC, retry with the
explicit OpenMC interpreter above before concluding the environment is missing
dependencies.

## Documentation Conventions

- Root `README.md`: repo overview and workflow
- `models/*/MODEL.md`: canonical model handoff docs
- `studies/*/report.md`: study-level findings
- `requests/*/*summary.md`: request-specific output

## YouTrack

YouTrack integration lives under `critbuddy/integrations/youtrack/`. Requests
are stored under `requests/CB-*/`.
