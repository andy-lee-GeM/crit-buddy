# AD-7 Piping Study

This request packages the canonical OpenMC piping models into runnable sweeps
for the three knobs called out in `AD-7`:

- fill ratio
- pipe spacing
- standard NPS pipe size

## Configs

- `configs/01_single_pipe_fill_fraction.yaml`
  Single isolated pipe fill-fraction sweep using the canonical `pipe-unit-cell`
  model.
- `configs/02_single_pipe_nps_sizes.yaml`
  Single isolated pipe sweep across standard NPS sizes using the same radial
  gas-gap assumption as the MCNP-derived reference model.
- `configs/03_two_pipe_spacing.yaml`
  Two-pipe reflected-water array sweep across edge spacing for the canonical
  `NPS 4` reference geometry.
- `configs/04_two_pipe_nps_fill_sensitivity.yaml`
  Two-pipe reflected-water sensitivity sweep across standard NPS sizes and fill
  fractions at a fixed edge spacing.

## Run

Use the OpenMC environment documented in `CLAUDE.md`:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python run_study.py requests/AD-7/configs/01_single_pipe_fill_fraction.yaml
/home/gem/.local/miniforge3/envs/openmc-env/bin/python run_study.py requests/AD-7/configs/03_two_pipe_spacing.yaml
```

To validate geometry before a long run:

```bash
/home/gem/.local/miniforge3/envs/openmc-env/bin/python - <<'PY'
from pathlib import Path
from critbuddy.runner import validate_geometry

validate_geometry(Path("requests/AD-7/configs/03_two_pipe_spacing.yaml"))
PY
```
