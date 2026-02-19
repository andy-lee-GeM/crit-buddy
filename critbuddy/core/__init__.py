"""
Core utilities for crit-buddy.

Provides configuration loading and shared material definitions.
"""

from .config import ExperimentConfig, Case, generate_cases, expand_sweeps
from .template import ProblemTemplate, ParameterSpec
from .materials import (
    create_uf6,
    create_aluminum,
    create_steel,
    create_water,
    create_concrete,
    create_air,
    mcnp_uf6,
    mcnp_aluminum,
    mcnp_steel,
    mcnp_water,
    mcnp_concrete,
    mcnp_air,
    get_material,
    get_density,
    MATERIAL_REGISTRY,
)

__all__ = [
    "ExperimentConfig",
    "Case",
    "generate_cases",
    "expand_sweeps",
    "ProblemTemplate",
    "ParameterSpec",
    "create_uf6",
    "create_aluminum",
    "create_steel",
    "create_water",
    "create_concrete",
    "create_air",
    "mcnp_uf6",
    "mcnp_aluminum",
    "mcnp_steel",
    "mcnp_water",
    "mcnp_concrete",
    "mcnp_air",
    "get_material",
    "get_density",
    "MATERIAL_REGISTRY",
]
