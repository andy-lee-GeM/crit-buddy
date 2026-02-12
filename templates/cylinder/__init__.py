"""
Cylinder Problem Template.

A vertical cylinder filled with UF6, surrounded by a wall and reflector.
User specifies physical dimensions (radius, height). For standard shipping
cylinder dimensions, use the shipping_cylinder template instead.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CylinderTemplate(ProblemTemplate):
    """
    Vertical cylinder with fissile material, wall, and reflector.

    Geometry:
        - Inner cylinder: UF6 (fissile material)
        - Wall: Aluminum or steel container
        - Reflector: Water or concrete surrounding the cylinder
    """

    PARAMETERS = {
        "enrichment": ParameterSpec(
            type="float",
            default=5.0,
            min=0.7,
            max=100.0,
            unit="wt%",
            description="U-235 enrichment (weight percent)",
        ),
        "radius_cm": ParameterSpec(
            type="float",
            required=True,
            min=0.1,
            max=100.0,
            unit="cm",
            description="Inner cylinder radius",
        ),
        "height_cm": ParameterSpec(
            type="float",
            default=100.0,
            min=1.0,
            max=500.0,
            unit="cm",
            description="Cylinder height",
        ),
        "wall_material": ParameterSpec(
            type="enum",
            options=["aluminum", "steel"],
            default="aluminum",
            description="Container wall material",
        ),
        "wall_thickness_cm": ParameterSpec(
            type="float",
            default=0.3175,  # 1/8 inch
            min=0.0,
            max=5.0,
            unit="cm",
            description="Wall thickness",
        ),
        "reflector_material": ParameterSpec(
            type="enum",
            options=["water", "concrete", "air", "none"],
            default="water",
            description="Reflector material",
        ),
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Reflector thickness",
        ),
        "uf6_density": ParameterSpec(
            type="float",
            default=5.09,
            min=1.0,
            max=6.0,
            unit="g/cc",
            description="UF6 density",
        ),
    }

    SIMULATION = {
        "PARTICLES": 10000,
        "BATCHES": 150,
        "INACTIVE": 50,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        """
        Compute geometry and physics parameters from user inputs.

        Args:
            p: Dictionary with user parameters (lowercase keys)

        Returns:
            Dictionary with derived parameters (uppercase keys for solver compatibility)
        """
        # Radii
        R1 = p["radius_cm"]
        R2 = R1 + p["wall_thickness_cm"]

        refl_thickness = p["reflector_thickness_cm"]
        if p["reflector_material"] == "none":
            refl_thickness = 0.0
        R3 = R2 + refl_thickness

        # Z coordinates
        Z_BOTTOM = 0.0
        Z_TOP = p["height_cm"]
        Z_REFL_BOTTOM = -refl_thickness
        Z_REFL_TOP = p["height_cm"] + refl_thickness

        # UF6 z-bounds (accounting for wall caps at top and bottom)
        wall_thickness = p["wall_thickness_cm"]
        Z_UF6_BOTTOM = Z_BOTTOM + wall_thickness
        Z_UF6_TOP = Z_TOP - wall_thickness

        # Source position (center of cylinder)
        KSRC_Z = p["height_cm"] / 2.0

        # Material densities (from registry)
        from critbuddy.core.materials import get_density

        wall_density = get_density(p["wall_material"])
        if p["reflector_material"] != "none":
            refl_density = get_density(p["reflector_material"])
        else:
            refl_density = 0.0

        return {
            # Geometry (uppercase for solver/template compatibility)
            "R1": R1,
            "R2": R2,
            "R3": R3,
            "Z_BOTTOM": Z_BOTTOM,
            "Z_TOP": Z_TOP,
            "Z_REFL_BOTTOM": Z_REFL_BOTTOM,
            "Z_REFL_TOP": Z_REFL_TOP,
            "Z_UF6_BOTTOM": Z_UF6_BOTTOM,
            "Z_UF6_TOP": Z_UF6_TOP,
            "KSRC_Z": KSRC_Z,
            # Pass through user params with uppercase keys
            "ENRICHMENT": p["enrichment"],
            "UF6_DENSITY": p["uf6_density"],
            "HEIGHT_CM": p["height_cm"],
            "REFL_THICKNESS": refl_thickness,
            "WALL_THICKNESS": p["wall_thickness_cm"],
            # Material info
            "WALL_MATERIAL": p["wall_material"],
            "WALL_DENSITY": wall_density,
            "REFLECTOR_MATERIAL": p["reflector_material"],
            "REFL_DENSITY": refl_density,
        }

    def get_plot_spec(self, dims: dict):
        """Custom PlotSpec for single cylinder visualization."""
        from critbuddy.reporting.plot_spec import PlotSpec

        r_outer = dims["r_outer"]
        height = dims["height"]
        refl = dims["refl_thickness"]

        # Center at middle of cylinder
        center = (0.0, 0.0, height / 2)

        # Width includes full diameter plus some padding
        padding = 1.1
        width = (
            r_outer * 2 * padding,
            r_outer * 2 * padding,
            (height + 2 * refl) * padding,
        )

        return PlotSpec(
            center=center,
            width=width,
            up_axis="z",
            exclude_materials=["Air", "Water"],  # Hide environment for cleaner visualization
        )


# Export the template class
Template = CylinderTemplate
