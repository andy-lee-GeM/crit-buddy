# MCNP Conversion API

## Overview

The `MCNPMaterial` class provides a clean interface for converting OpenMC materials to MCNP format. It encapsulates all necessary conversions including ZAID formatting, density calculations, and nuclide data.

## Quick Start

```python
from critbuddy.core.materials import MCNPMaterial, water

# Convert OpenMC material to MCNP format
mat = water()
mcnp = MCNPMaterial.from_openmc(mat, xs_suffix="80c")

# Access MCNP-ready data
print(mcnp.cell_density_g_cm3)    # -1.0 (negative for g/cm³)
print(mcnp.cell_density_bcm)      # +0.06723 (positive for atoms/b-cm)

# Iterate over nuclides
for nuc in mcnp.nuclides:
    print(f"{nuc.zaid:12s}  {nuc.atom_density_bcm:.8e}")
```

## API Reference

### `MCNPMaterial` Class

Main entry point for OpenMC → MCNP conversion.

#### Factory Method

```python
MCNPMaterial.from_openmc(material, xs_suffix="80c") -> MCNPMaterial
```

**Parameters:**
- `material`: OpenMC material to convert
- `xs_suffix`: MCNP cross-section library suffix (default: "80c")
  - `"80c"` = ENDF/B-VIII.0
  - `"70c"` = ENDF/B-VII.0
  - `"31c"` = ENDF/B-VII.1

**Returns:** `MCNPMaterial` with all MCNP-ready data

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Material name |
| `bulk_density_g_cm3` | `float` | Total bulk density (positive) |
| `cell_density_g_cm3` | `float` | **MCNP cell card density (negative)** |
| `total_atom_density_bcm` | `float` | Total atom density (positive) |
| `cell_density_bcm` | `float` | **MCNP cell card density (positive)** |
| `xs_suffix` | `str` | Cross-section suffix used |
| `nuclides` | `tuple[MCNPNuclide, ...]` | List of nuclides |

#### Methods

```python
mcnp.get_nuclide_by_name(name: str) -> MCNPNuclide | None
```
Find nuclide by OpenMC name (e.g., "U235").

```python
mcnp.get_nuclide_by_zaid(zaid: str) -> MCNPNuclide | None
```
Find nuclide by MCNP ZAID (e.g., "92235.80c").

```python
mcnp.to_dict() -> dict
```
Export to dictionary for JSON serialization.

---

### `MCNPNuclide` Class

Per-nuclide MCNP data.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `nuclide` | `str` | OpenMC name (e.g., "U235") |
| `zaid` | `str` | **MCNP ZAID (e.g., "92235.80c")** |
| `atomic_mass_g_mol` | `float` | Atomic mass |
| `atom_density_bcm` | `float` | **MCNP material card value** |
| `atom_fraction` | `float` | Normalized atom fraction (0-1) |
| `mass_density_g_cm3` | `float` | Mass density for this nuclide |
| `weight_fraction` | `float` | Normalized weight fraction (0-1) |

#### Methods

```python
nuc.to_dict() -> dict
```
Export to dictionary.

---

## Usage Examples

### Example 1: Generate MCNP Material Card

```python
from critbuddy.core.materials import MCNPMaterial, uo2f2
from critbuddy.core.materials.uo2f2_physics import uo2f2_density

# Create material
density = uo2f2_density(h_to_u=10.0, enrichment_pct=5.0)
mat = uo2f2(enrichment_pct=5.0, h_to_u=10.0, density=density)

# Convert to MCNP
mcnp = MCNPMaterial.from_openmc(mat)

# Print MCNP format
print(f"c --- Material: {mcnp.name}")
print(f"c     Density: {mcnp.cell_density_g_cm3:.6f} g/cm³")
print(f"m1", end="")
for nuc in mcnp.nuclides:
    print(f"  {nuc.zaid:12s}  {nuc.atom_density_bcm:.8e}    $ {nuc.nuclide}")
```

**Output:**
```
c --- Material: UO2F2
c     Density: -1.523400 g/cm³
m1  92235.80c  1.23000000e-04    $ U235
    92238.80c  4.87000000e-03    $ U238
    8016.80c   3.70200000e-03    $ O16
    9019.80c   1.23400000e-03    $ F19
    1001.80c   6.17000000e-02    $ H1
```

### Example 2: Query Specific Nuclides

```python
mcnp = MCNPMaterial.from_openmc(material)

# Find by name
u235 = mcnp.get_nuclide_by_name("U235")
print(f"U235 ZAID: {u235.zaid}")
print(f"U235 density: {u235.atom_density_bcm:.8e} atoms/b-cm")

# Find by ZAID
h1 = mcnp.get_nuclide_by_zaid("1001.80c")
print(f"H1 fraction: {h1.atom_fraction:.6f}")
```

### Example 3: Process Multiple Materials

```python
from critbuddy.core.materials import MCNPMaterial, water, aluminum, stainless_steel_316

materials = [water(), aluminum(), stainless_steel_316()]

for mat in materials:
    mcnp = MCNPMaterial.from_openmc(mat)
    print(f"\n{mcnp.name}:")
    print(f"  Density: {mcnp.cell_density_g_cm3:.4f} g/cm³")
    print(f"  Nuclides: {', '.join(nuc.zaid for nuc in mcnp.nuclides)}")
```

### Example 4: Export to JSON

```python
import json

mcnp = MCNPMaterial.from_openmc(material)
data = mcnp.to_dict()

# Save to file
with open("material.json", "w") as f:
    json.dump(data, f, indent=2)
```

---

## ZAID Format

MCNP uses ZAID (Z-A-ID) format to identify nuclides:

**Format:** `ZZZAAA.xxc`

- **ZZZ**: Atomic number (Z)
- **AAA**: Mass number (A)
- **.xxc**: Cross-section library suffix

**Examples:**

| OpenMC | ZAID | Element |
|--------|------|---------|
| `U235` | `92235.80c` | Uranium-235 |
| `U238` | `92238.80c` | Uranium-238 |
| `O16` | `8016.80c` | Oxygen-16 |
| `H1` | `1001.80c` | Hydrogen-1 |
| `F19` | `9019.80c` | Fluorine-19 |

**Calculation:** `ZAID_number = 1000 × Z + A`

---

## MCNP Cell Card Densities

MCNP uses **signed densities** in cell cards:

### Negative (g/cm³)
```
1  1  -1.52  ...    $ negative = mass density
```
Use: `mcnp.cell_density_g_cm3`

### Positive (atoms/barn-cm)
```
1  1  +0.067234  ...    $ positive = atom density
```
Use: `mcnp.cell_density_bcm`

**Both are equivalent** in MCNP. Choose based on preference.

---

## Integration with Existing Code

### Scripts

Scripts should use `MCNPMaterial` instead of manual conversions:

```python
# Old way (manual)
summary = summarize_openmc_material(mat)
for row in summary.nuclides:
    zaid = _zaid(row.nuclide, "80c")
    print(f"{zaid}  {row.atom_density_bcm}")

# New way (clean)
mcnp = MCNPMaterial.from_openmc(mat)
for nuc in mcnp.nuclides:
    print(f"{nuc.zaid}  {nuc.atom_density_bcm}")
```

### Reports

```python
mcnp = MCNPMaterial.from_openmc(material)

# Generate markdown table
print(f"| Nuclide | ZAID | Atom Density (atoms/b-cm) |")
print(f"|---------|------|---------------------------|")
for nuc in mcnp.nuclides:
    print(f"| {nuc.nuclide} | {nuc.zaid} | {nuc.atom_density_bcm:.8e} |")
```

---

## Architecture

```
critbuddy/core/materials/
├── material_specs.py         # Static material definitions
├── material_properties.py    # Density/fraction conversions
├── uo2f2_physics.py          # UO2F2 physics calculations
├── builders.py               # OpenMC material builders
└── mcnp_conversion.py        # ✨ NEW: OpenMC → MCNP conversion
```

**Design principles:**
- ✅ Single source of truth for conversions
- ✅ Clean, reusable API
- ✅ No breaking changes to existing code
- ✅ Scripts use the library (not vice versa)

---

## Testing

Run the test script:
```bash
python test_mcnp_conversion.py
```

Or run the example:
```bash
python examples/mcnp_material_conversion.py
```

---

## Future Extensions

The `MCNPMaterial` class is designed to be extended:

1. **Formatting methods** (in scripts, not the class):
   - `format_mcnp_card(mcnp)` → MCNP text
   - `format_markdown_table(mcnp)` → Markdown

2. **H/U sweep utilities**:
   - Generate H/U density tables
   - Material comparisons

3. **Validation**:
   - Check material validity
   - Warn about unsupported features
