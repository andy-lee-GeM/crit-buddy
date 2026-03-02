# Assumptions Template for MCNP Reproduction

Use this template to produce a complete assumptions inventory.

## Experiment metadata
- Config path:
- Experiment name:
- Template/problem:
- Date of extraction:
- Git commit or branch:
- Solver used:
- Nuclear data library and temperature:

## Inputs and sweeps
- Fixed parameters:
- Swept parameters and values:
- Total case count:
- Defaulted parameters pulled from template:

## Derived geometry (units: cm)
- Coordinate system and origin conventions:
- Array configuration:
- Cylinder geometry:
- Spacing and gaps:
- Derived array dimensions:
- Reflector thickness:
- Bounding box surfaces and values:
- Source distribution box:
- Partial fill interpretation:

## Materials
- Fissile material composition and density:
- Enrichment basis and isotope set:
- Wall material composition and density:
- Environment material composition and density:
- Void or headspace material composition and density:
- Thermal scattering assignments:

## Boundary conditions and environment
- Boundary type:
- Reflector or surrounding medium assumptions:
- Environment fill regions and exclusions:

## Physics and run settings
- Run mode:
- Particles per batch:
- Total batches:
- Inactive batches:
- Total active histories:
- Source definition:
- Tallies or output quantities (if any):

## MCNP translation checklist
- Surfaces defined and labeled:
- Cell region logic matches OpenMC:
- Material cards with correct atom fractions:
- `MT` cards for thermal scattering:
- `KCODE` and `KSRC` or `SDEF` settings:
- Boundary conditions applied:

## Global modeling assumptions
- Temperature and cross-section defaults:
- No burnup or depletion:
- No absorbers or poisons credited:
- Isotopic simplifications:

## Open questions
- Unknown inputs or defaults:
- Items needing user confirmation:
