# Source Files Checklist

Use this checklist to locate assumptions and defaults.

## Always check
- Experiment YAML: `experiments/crit_requests/**/_config/*.yaml`
- Template defaults and derivations: `templates/<problem>/__init__.py`
- OpenMC geometry and settings: `templates/<problem>/openmc/model.py`
- Material definitions and thermal scattering: `critbuddy/core/materials.py`
- Global modeling assumptions: `docs/criticality-assumptions.md`
- Cross section path and MCNP executable: `config.yaml`
- Solver environment setup: `critbuddy/runner.py`

## If present
- Validation artifacts: `_validation/materials.xml`, `_validation/geometry.xml`, `_validation/plots.xml`
- Report or results summary: `results/*.md`, `results/REPORT.md`, `results/RESULTS_SUMMARY.md`
- Run configs: `runs/**/config.yaml`
