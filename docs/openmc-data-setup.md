# OpenMC Data Setup

Crit-Buddy does not vendor OpenMC nuclear data. Each developer environment needs a
local or mounted HDF5 library, and `config.yaml` must point to its
`cross_sections.xml`.

## What the Repo Uses

Crit-Buddy reads `openmc_cross_sections` from `config.yaml`. When
`OPENMC_CROSS_SECTIONS` is not already set, `run_study.py` exports that path for the
current process before OpenMC runs.

The path must point to `cross_sections.xml`, not just the parent directory.

## Reuse the Existing Library First

The currently configured workstation uses:

```text
/home/andylee/openmc_data/endfb-vii.1-hdf5/cross_sections.xml
```

That `endfb-vii.1-hdf5` directory is about 5.9 GB unpacked. If your dev environment
can see the same filesystem, reuse that directory directly. If it cannot, copy the
entire `endfb-vii.1-hdf5` directory into a local data location such as
`~/openmc_data/endfb-vii.1-hdf5`.

Example copy from another configured Linux or WSL environment:

```bash
mkdir -p ~/openmc_data
rsync -av --progress <configured-host>:/home/andylee/openmc_data/endfb-vii.1-hdf5 ~/openmc_data/
```

Any transfer mechanism is fine as long as the copied directory still contains:

```text
endfb-vii.1-hdf5/
  cross_sections.xml
  neutron/
  photon/
  wmp/
```

## Point Crit-Buddy at the Library

Create a local `config.yaml` if you do not already have one:

```bash
cp config.yaml.example config.yaml
```

Set `openmc_cross_sections` to the XML file inside the copied or mounted library:

```yaml
conda_env: openmc-env
openmc_cross_sections: /home/<user>/openmc_data/endfb-vii.1-hdf5/cross_sections.xml
```

If your dev environment uses the same path as the configured workstation, you can use:

```yaml
openmc_cross_sections: /home/andylee/openmc_data/endfb-vii.1-hdf5/cross_sections.xml
```

You can also set the shell environment variable yourself:

```bash
export OPENMC_CROSS_SECTIONS=/home/<user>/openmc_data/endfb-vii.1-hdf5/cross_sections.xml
```

That is optional for normal Crit-Buddy runs because the runner already does it from
`config.yaml`.

## Verify the Setup

This uses the same config-loading path that Crit-Buddy uses at runtime:

```bash
python -c "from critbuddy.runner import load_config; load_config(); import os; from pathlib import Path; p = Path(os.environ['OPENMC_CROSS_SECTIONS']); print(p); print(p.exists())"
```

The command should print the resolved `cross_sections.xml` path and then `True`.

## Fallback: Download the Data

If you cannot reuse the existing library, download ENDF/B-VII.1 with OpenMC:

```bash
python -c "import openmc.data; openmc.data.download_nndc_data('endfb71')"
```

After the download completes, update `config.yaml` so `openmc_cross_sections` points
to the downloaded `cross_sections.xml`.
