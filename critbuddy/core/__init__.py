"""
Core utilities for crit-buddy.

Provides configuration loading and shared material definitions.
"""

from .config import ExperimentConfig, Case, generate_cases, expand_sweeps
from .template import ProblemTemplate, ParameterSpec
from .template_loader import load_template_class, load_template_module
from .materials import (
    create_uf6,
    create_uo2f2,
    create_fissile_material,
    create_environment_material,
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
    "load_template_class",
    "load_template_module",
    "create_uf6",
    "create_uo2f2",
    "create_fissile_material",
    "create_environment_material",
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
