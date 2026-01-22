"""
Core utilities for crit-buddy.

Provides configuration loading and shared material definitions.
"""

from .config import ExperimentConfig, Case, generate_cases, expand_sweeps
from .materials import (
    create_uf6,
    create_heu,
    create_aluminum,
    create_steel,
    create_water,
    create_concrete,
    create_air,
    mcnp_uf6,
    mcnp_heu,
    mcnp_aluminum,
    mcnp_steel,
    mcnp_water,
    mcnp_concrete,
    mcnp_air,
    get_material,
    get_density,
    DENSITY,
    MATERIAL_REGISTRY,
)

__all__ = [
    "ExperimentConfig",
    "Case",
    "generate_cases",
    "expand_sweeps",
    "create_uf6",
    "create_heu",
    "create_aluminum",
    "create_steel",
    "create_water",
    "create_concrete",
    "create_air",
    "mcnp_uf6",
    "mcnp_heu",
    "mcnp_aluminum",
    "mcnp_steel",
    "mcnp_water",
    "mcnp_concrete",
    "mcnp_air",
    "get_material",
    "get_density",
    "DENSITY",
    "MATERIAL_REGISTRY",
]
