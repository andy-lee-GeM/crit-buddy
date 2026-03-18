# Materials Reference Documentation

This directory contains technical basis documents for material property calculations used in crit-buddy.

## Documents

### [uo2f2-density-basis.md](./uo2f2-density-basis.md)
Technical basis for UO₂F₂ (uranyl fluoride) density calculations as a function of enrichment and H/U ratio.

**Source**: ORNL/TM-12292 (Jordan & Turner, 1992), Appendix A
**Implementation**: [`critbuddy/core/materials/uo2f2_physics.py`](../../../critbuddy/core/materials/uo2f2_physics.py)

#### Quick Reference

**For H/U < 4** (hydrated solids):
```
ρᵤ = 4.96 - 0.32 × (H/U)
```

**For H/U ≥ 4** (solutions/slurries):
```
ρᵤ = Mᵤ / [72.2809 + (H/U - 4) × 9.0287]
```

Where:
- ρᵤ = uranium density (g/cm³)
- Mᵤ = uranium molar mass at given enrichment (g/mol)
- H/U = hydrogen-to-uranium atomic ratio

#### Usage Example

```python
from critbuddy.core.materials.uo2f2_physics import uo2f2_density, uo2f2_stoichiometry

# Calculate bulk density
density = uo2f2_density(h_to_u=500.0, enrichment_pct=20.0)
# Returns: 1.539 g/cm³

# Get complete stoichiometry
stoich = uo2f2_stoichiometry(h_to_u=500.0, enrichment_pct=20.0)
# Returns: UO2F2Stoichiometry with all composition details
```

## Source Documents

Reference PDFs are stored in [`docs/references/`](../../):
- [`uo2f2-density-ornl-tm-12292.pdf`](../../uo2f2-density-ornl-tm-12292.pdf) - ORNL/TM-12292 full report
- [`material_reference_mcnp_pnnl-15870.pdf`](../../material_reference_mcnp_pnnl-15870.pdf) - General materials reference

## Related Code

### Material Physics
- [`critbuddy/core/materials/uo2f2_physics.py`](../../../critbuddy/core/materials/uo2f2_physics.py) - UO₂F₂ density and stoichiometry
- [`critbuddy/core/materials/material_properties.py`](../../../critbuddy/core/materials/material_properties.py) - General property conversions

### Material Builders
- [`critbuddy/core/materials/builders.py`](../../../critbuddy/core/materials/builders.py) - OpenMC material constructors
- [`critbuddy/core/materials/material_specs.py`](../../../critbuddy/core/materials/material_specs.py) - Static material definitions

### Tests
- [`tests/unit/materials/test_uo2f2_physics.py`](../../../tests/unit/materials/test_uo2f2_physics.py) - Density validation against ORNL data
- [`tests/unit/materials/test_properties.py`](../../../tests/unit/materials/test_properties.py) - General property tests

## Contributing

When adding new material property calculations:

1. **Add reference PDF** to `docs/references/`
2. **Create basis document** in `docs/references/materials/`
3. **Implement calculation** in appropriate module under `critbuddy/core/materials/`
4. **Add validation tests** under `tests/unit/materials/`
5. **Update this README** with links to new documents

## Validation

All material property calculations must be validated against published data:
- Include source document, table/equation numbers
- Test against at least 5 reference points spanning the valid range
- Document expected accuracy and conservative biases
