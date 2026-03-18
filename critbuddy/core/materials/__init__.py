"""
Public materials package API.
"""

from .builders import (
    MATERIAL_COLORS,
    MATERIAL_LIBRARY,
    MATERIAL_REGISTRY,
    air_dry,
    aluminum,
    concrete,
    concrete_ordinary,
    create_environment_material,
    create_fissile_material,
    create_hf,
    create_uf6,
    create_vacuum,
    get_color_legend,
    get_color_mapping,
    get_density,
    get_material,
    get_material_color,
    humid_air,
    stainless_steel_304,
    stainless_steel_316,
    uo2f2,
    uf6,
    vacuum,
    void,
    water,
)
from .material_specs import MATERIAL_ALIASES, MATERIAL_DENSITIES, MaterialSpec
