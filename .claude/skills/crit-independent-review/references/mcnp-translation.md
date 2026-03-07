# OpenMC to MCNP Translation Notes

Use this as a mapping guide when converting an OpenMC model into MCNP input.

## Surfaces
- `openmc.XPlane(x0=a)` maps to `px a`.
- `openmc.YPlane(y0=b)` maps to `py b`.
- `openmc.ZPlane(z0=c)` maps to `pz c`.
- `openmc.ZCylinder(x0, y0, r)` maps to `c/z x0 y0 r`.

## Regions and senses
- OpenMC uses `-surface` for the negative half-space and `+surface` for the positive half-space.
- MCNP cell cards use the same sign convention.

## Boundary conditions
- `boundary_type = reflective` maps to reflecting boundaries on the outer surfaces.
- In MCNP6, prefix the surface with `*` to make it reflecting.
- `boundary_type = vacuum` maps to a normal boundary with an outside cell `imp:n=0`.

## Materials and thermal scattering
- OpenMC atom fractions map to MCNP atom fractions in the `m` card.
- For bound hydrogen in water, use `mt` with `lwtr` at the matching temperature.
- For UO2F2 with H, apply the `lwtr` thermal scattering to that material as well.
- Match the cross-section library between OpenMC and MCNP. OpenMC uses whatever is in `OPENMC_CROSS_SECTIONS`.

## Source and eigenvalue settings
- `openmc.Settings.run_mode = eigenvalue` maps to `KCODE` in MCNP.
- OpenMC `IndependentSource(Box)` maps to `KSRC` points inside the fissile volume or an `SDEF` with a uniform box distribution.

## Units
- OpenMC uses cm for geometry and g/cm3 for densities.
- MCNP uses the same units by default.
