"""
Shipping Cylinder Problem Template.

UF6 shipping/storage cylinders (5A, 5B, 30B, 48X, 48Y, etc.) with dimensions
automatically loaded from the ANSI N14.1 cylinder registry.

For user-specified dimensions, use the cylinder template instead.
"""

import math

from critbuddy.core.template import ProblemTemplate, ParameterSpec
from critbuddy.core.geometry.cylinders import CYLINDER_REGISTRY


class ShippingCylinderTemplate(ProblemTemplate):
    """
    UF6 shipping/storage cylinder with registry-based dimensions.

    Dimensions are automatically populated from the cylinder registry based on
    the selected cylinder_type. Wall material is also determined by the registry.

    Geometry:
        - Inner cylinder: UF6 (fissile material)
        - Wall: Material from registry (Monel for 5A/5B, carbon steel for larger)
        - Reflector: Water or air surrounding the cylinder
    """

    PARAMETERS = {
        # Fissile material
        "enrichment": ParameterSpec(
            type="float",
            required=True,
            min=0.7,
            max=100.0,
            unit="wt%",
            description="U-235 enrichment (weight percent)",
        ),
        "fissile_material": ParameterSpec(
            type="enum",
            options=["uf6", "uo2f2"],
            default="uf6",
            description="Fissile material type",
        ),
        "fissile_density": ParameterSpec(
            type="float",
            default=None,
            min=1.0,
            max=7.0,
            unit="g/cc",
            description="Optional fissile material density override (UF6 default: 5.09)",
        ),
        "h_to_u": ParameterSpec(
            type="float",
            default=0.0,
            min=0.0,
            max=500.0,
            description="H/U atomic ratio for UO2F2 (0 = dry)",
        ),
        "fill_fraction": ParameterSpec(
            type="float",
            default=1.0,
            min=0.01,
            max=1.5,
            description="Fill fraction (1.0 = full, >1.0 = over-fill)",
        ),
        # Cylinder type (dimensions from registry)
        "cylinder_type": ParameterSpec(
            type="enum",
            options=list(CYLINDER_REGISTRY.keys()),
            required=True,
            description="Cylinder type - dimensions from ANSI N14.1 specs",
        ),
        # Environment
        "environment_material": ParameterSpec(
            type="enum",
            options=["water", "air", "none"],
            default="water",
            description="Environment/reflector material",
        ),
        "environment_density": ParameterSpec(
            type="float",
            default=None,
            min=0.00001,
            max=3.0,
            unit="g/cc",
            description="Optional environment density override",
        ),
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Reflector thickness (30 cm = full reflection)",
        ),
    }

    SIMULATION = {
        "PARTICLES": 10000,
        "BATCHES": 200,
        "INACTIVE": 50,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        """
        Compute geometry parameters from user inputs and cylinder registry.

        The cylinder_type parameter is used to look up standard dimensions
        from the registry. Other parameters (enrichment, density, reflector)
        are user-specified.

        Geometry layers (inside to outside):
        1. UF6 fissile region
        2. Cylinder wall (material from registry)
        3. External reflector (optional)
        """
        from critbuddy.core.geometry.cylinders import get_cylinder, get_inner_radius
        from critbuddy.core.materials import get_density

        # Get cylinder specs from registry
        spec = get_cylinder(p["cylinder_type"])

        # Cylinder dimensions from registry
        r_inner = get_inner_radius(p["cylinder_type"])
        h_internal = spec.internal_height_cm
        wall_t = spec.wall_thickness_cm
        wall_material = spec.wall_material

        # Apply fill fraction to height (for over-fill scenarios)
        fill_fraction = p["fill_fraction"]
        uf6_height = h_internal * fill_fraction
        total_fuel_volume_cm3 = math.pi * r_inner**2 * h_internal
        fill_volume_cm3 = total_fuel_volume_cm3 * fill_fraction

        # Build up radii from inside out
        r_wall_outer = r_inner + wall_t

        # Environment/Reflector
        environment_material = p.get("environment_material", "water")
        environment_density = p.get("environment_density")
        refl_t = p["reflector_thickness_cm"]
        if environment_material == "none":
            refl_t = 0.0
        r_refl_outer = r_wall_outer + refl_t

        # Z coordinates
        # Cylinder sits from z=0 to z=h_internal (internal cavity)
        # Wall caps add thickness at top and bottom
        z_bottom = 0.0
        z_top = h_internal
        z_refl_bottom = -refl_t if refl_t > 0 else 0.0
        z_refl_top = h_internal + refl_t

        # UF6 z-bounds (accounting for wall caps)
        z_uf6_bottom = wall_t
        z_uf6_top = min(wall_t + uf6_height, h_internal - wall_t)

        # Source position (center of UF6 region)
        ksrc_z = (z_uf6_bottom + z_uf6_top) / 2.0

        # Material densities
        wall_density = get_density(wall_material)
        if environment_material == "none":
            env_density = 0.0
        elif environment_density is not None:
            env_density = environment_density
        else:
            env_density = get_density(environment_material)

        # Fissile material
        fissile_material = p.get("fissile_material", "uf6")
        fissile_density = p.get("fissile_density")
        h_to_u = p.get("h_to_u", 0.0)

        return {
            # Cylinder type info (for reporting)
            "CYLINDER_TYPE": p["cylinder_type"].upper(),
            "CYLINDER_NAME": spec.name,

            # Fissile material
            "ENRICHMENT": p["enrichment"],
            "FISSILE_MATERIAL": fissile_material,
            "FISSILE_DENSITY": fissile_density,
            "H_TO_U": h_to_u,
            "FILL_FRACTION": fill_fraction,
            "TOTAL_FUEL_VOLUME_CM3": total_fuel_volume_cm3,
            "TOTAL_FUEL_VOLUME_L": total_fuel_volume_cm3 / 1000.0,
            "FILL_VOLUME_CM3": fill_volume_cm3,
            "FILL_VOLUME_L": fill_volume_cm3 / 1000.0,

            # Cylinder radii
            "R_INNER": r_inner,
            "R_WALL_OUTER": r_wall_outer,
            "R_REFL_OUTER": r_refl_outer,

            # Z coordinates
            "Z_BOTTOM": z_bottom,
            "Z_TOP": z_top,
            "Z_FISSILE_BOTTOM": z_uf6_bottom,
            "Z_FISSILE_TOP": z_uf6_top,
            "Z_REFL_BOTTOM": z_refl_bottom,
            "Z_REFL_TOP": z_refl_top,

            # Wall
            "WALL_MATERIAL": wall_material,
            "WALL_THICKNESS": wall_t,
            "WALL_DENSITY": wall_density,

            # Environment
            "ENVIRONMENT_MATERIAL": environment_material,
            "ENV_DENSITY": env_density,
            "REFL_THICKNESS": refl_t,

            # Dimensions
            "HEIGHT_CM": h_internal,
            "UF6_HEIGHT": z_uf6_top - z_uf6_bottom,

            # Source
            "KSRC_Z": ksrc_z,
        }


# Export the template class
Template = ShippingCylinderTemplate
