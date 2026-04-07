"""
Declarative specifications for shared static materials.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MaterialSpec:
    """Declarative definition for a static material."""

    name: str
    density_g_cm3: float
    fraction_basis: str
    components: dict[str, float]
    sab: tuple[str, ...] = ()


STATIC_MATERIAL_SPECS = {
    "aluminum": MaterialSpec(
        name="Aluminum",
        density_g_cm3=2.70,
        fraction_basis="wo",
        components={"Al": 1.0},
    ),
    "stainless_steel_304": MaterialSpec(
        name="Stainless_Steel_304",
        density_g_cm3=7.93,
        fraction_basis="wo",
        components={
            "Fe56": 0.70,
            "Cr52": 0.19,
            "Ni58": 0.10,
            "Mn55": 0.01,
        },
    ),
    "stainless_steel_316": MaterialSpec(
        name="Stainless_Steel_316",
        density_g_cm3=8.00,
        fraction_basis="wo",
        components={
            "Fe": 0.68,
            "Cr": 0.17,
            "Ni": 0.12,
            "Mo": 0.025,
            "Mn": 0.005,
        },
    ),
    "concrete_ordinary": MaterialSpec(
        name="Concrete",
        density_g_cm3=2.30,
        fraction_basis="wo",
        components={
            "H": 0.01,
            "O": 0.53,
            "Si": 0.34,
            "Ca": 0.04,
            "Al": 0.03,
            "Fe": 0.01,
        },
    ),
    "water": MaterialSpec(
        name="Water",
        density_g_cm3=1.0,
        fraction_basis="ao",
        components={"H1": 2.0, "O16": 1.0},
        sab=("c_H_in_H2O",),
    ),
    "air_dry": MaterialSpec(
        name="Air",
        density_g_cm3=0.001225,
        fraction_basis="ao",
        components={"N14": 0.78, "O16": 0.21, "Ar40": 0.01},
    ),
    "humid_air": MaterialSpec(
        name="Humid_Air",
        density_g_cm3=0.00119,
        fraction_basis="ao",
        components={"N14": 0.77, "O16": 0.2084, "Ar40": 0.009, "H1": 0.005},
    ),
    "void": MaterialSpec(
        name="Void",
        density_g_cm3=0.0001,
        fraction_basis="ao",
        components={"N14": 0.78, "O16": 0.21, "Ar40": 0.01},
    ),
    "vacuum": MaterialSpec(
        name="Vacuum",
        density_g_cm3=1.0e-10,
        fraction_basis="ao",
        components={"N14": 1.0},
    ),
}


MATERIAL_DENSITIES = {
    key: spec.density_g_cm3
    for key, spec in STATIC_MATERIAL_SPECS.items()
}


MATERIAL_ALIASES = {
    "air": "air_dry",
    "aluminum_6061": "aluminum",
    "concrete": "concrete_ordinary",
    "ss304": "stainless_steel_304",
    "steel": "stainless_steel_316",
}
