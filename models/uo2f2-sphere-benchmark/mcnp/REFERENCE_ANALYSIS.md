# MCNP Reference Case Analysis

## Model Overview

**Title:** UO2F2 Sphere Benchmark - 20 wt% H/X=100 Vacuum Boundary  
**Configuration:** homogeneous `UO2F2-H2O` fuel sphere with water reflector

## Geometry Parameters

- Fuel radius: `13.88 cm`
- Reflector thickness: `100.0 cm`
- Outer radius: `113.88 cm`
- Outer boundary: `vacuum`

This matches the fixed-radius OpenMC benchmark point used in:

- `studies/ornl-tm-12292-uo2f2-20pct-sphere/configs/02_hx_validation_sweep.yaml`
- `case_6` in `runs/02_hx_validation_sweep/latest/results.csv`

## Materials

### Material 1: UO2F2-H2O fuel

- Enrichment: `20.0 wt% U-235`
- Paper moderation point: `H/X = 100`
- Exact shared-builder moderation value: `H/U = 20.204171182632887`
- Bulk density: `2.23908638 g/cm3`
- Thermal scattering: `lwtr.01t`

Fuel material card values were derived from the shared crit-buddy material path with:

```bash
python scripts/get_mcnp_density.py uo2f2 --no-default-sweeps -e 20.0 --h-to-u 20.204171182632887
```

### Material 2: Water reflector

- Density: `1.0 g/cm3`
- Thermal scattering: `lwtr.01t`

Reflector material card values match the shared water builder path:

```bash
python scripts/get_mcnp_density.py water --no-default-sweeps
```

## Criticality Settings

- Mode: neutron transport
- KCODE: `6000` particles/cycle, `40` inactive, `180` total cycles
- Source: point source at the sphere center

The `kcode` settings were chosen to match the OpenMC case settings as closely
as practical (`6000` particles, `180` batches, `40` inactive).

## Comparison Target

The matching OpenMC point is:

- `H/X = 100`
- exact `H/U = 20.204171`
- `k-eff = 0.99369 +/- 0.00113`

This MCNP deck is intended as a single-case parity check against that OpenMC
benchmark point, not as a reproduction of ORNL Table B.1 `k4`.

## Run Result

Manual MCNP run on April 10, 2026:

- Command: `mcnp6 i=<model.inp> o=<model_hx100_vacuum.out> tasks 4`
- Output: `mcnp/model_hx100_vacuum.out`
- Final MCNP `k-eff`: `0.98962 +/- 0.00101`

Observed OpenMC vs MCNP difference for this point:

- OpenMC `k-eff`: `0.99369 +/- 0.00113`
- MCNP `k-eff`: `0.98962 +/- 0.00101`
- Delta `k-eff`: `-0.00407` (`-406.7 pcm`, MCNP lower)
- Combined `1σ`: `0.00151`

So for this single benchmark point, MCNP comes in about `2.7σ` lower than the
matching OpenMC result while preserving the same overall order of magnitude and
subcritical / near-critical behavior.
