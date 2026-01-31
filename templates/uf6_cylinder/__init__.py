"""
UF6 Shipping Cylinder Problem Template.

A unified template for UF6 shipping/storage cylinders (5A, 5B, 30B, 48X, 48Y, etc.).
Cylinder dimensions are automatically loaded from the cylinder registry based on
the cylinder_type parameter.

This replaces separate templates for each cylinder type with a single parametric
template that handles all standard cylinder configurations.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec
from critbuddy.core.cylinders import CYLINDER_REGISTRY


class UF6CylinderTemplate(ProblemTemplate):
    """
    Generic UF6 shipping/storage cylinder.

    Dimensions are automatically populated from the cylinder registry based on
    the selected cylinder_type. Wall material is also determined by the registry.

    Geometry:
        - Inner cylinder: UF6 (fissile material)
        - Wall: Material from registry (Monel for 5A/5B, carbon steel for larger)
        - Reflector: Water or air surrounding the cylinder
    """

    PARAMETERS = {
        "cylinder_type": ParameterSpec(
            type="enum",
            options=list(CYLINDER_REGISTRY.keys()),
            required=True,
            description="Cylinder type - dimensions loaded from ANSI N14.1 specs",
        ),
        "enrichment": ParameterSpec(
            type="float",
            required=True,
            min=0.7,
            max=100.0,
            unit="wt%",
            description="U-235 enrichment (weight percent)",
        ),
        "uf6_density": ParameterSpec(
            type="float",
            default=5.09,
            min=1.0,
            max=6.0,
            unit="g/cc",
            description="UF6 density",
        ),
        "fill_fraction": ParameterSpec(
            type="float",
            default=1.0,
            min=0.1,
            max=1.5,
            description="Fill fraction (1.0 = full height, >1.0 = over-fill)",
        ),
        "reflector_material": ParameterSpec(
            type="enum",
            options=["water", "air", "none"],
            default="water",
            description="External reflector material",
        ),
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=0.0,
            max=100.0,
            unit="cm",
            description="External reflector thickness (30 cm = full reflection)",
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
        from critbuddy.core.cylinders import get_cylinder, get_inner_radius
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

        # Build up radii from inside out
        r_wall_outer = r_inner + wall_t

        # External reflector
        refl_t = p["reflector_thickness_cm"]
        if p["reflector_material"] == "none":
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
        refl_density = get_density(p["reflector_material"]) if p["reflector_material"] != "none" else 0.0

        return {
            # Cylinder type info (for reporting)
            "CYLINDER_TYPE": p["cylinder_type"].upper(),
            "CYLINDER_NAME": spec.name,

            # Fissile material
            "ENRICHMENT": p["enrichment"],
            "UF6_DENSITY": p["uf6_density"],
            "FILL_FRACTION": fill_fraction,

            # Cylinder radii
            "R_INNER": r_inner,
            "R_WALL_OUTER": r_wall_outer,
            "R_REFL_OUTER": r_refl_outer,

            # Z coordinates
            "Z_BOTTOM": z_bottom,
            "Z_TOP": z_top,
            "Z_UF6_BOTTOM": z_uf6_bottom,
            "Z_UF6_TOP": z_uf6_top,
            "Z_REFL_BOTTOM": z_refl_bottom,
            "Z_REFL_TOP": z_refl_top,

            # Wall
            "WALL_MATERIAL": wall_material,
            "WALL_THICKNESS": wall_t,
            "WALL_DENSITY": wall_density,

            # Reflector
            "REFLECTOR_MATERIAL": p["reflector_material"],
            "REFL_THICKNESS": refl_t,
            "REFL_DENSITY": refl_density,

            # Dimensions
            "HEIGHT_CM": h_internal,
            "UF6_HEIGHT": z_uf6_top - z_uf6_bottom,

            # Source
            "KSRC_Z": ksrc_z,
        }


# Export the template class
Template = UF6CylinderTemplate
