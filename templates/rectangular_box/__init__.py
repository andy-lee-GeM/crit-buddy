"""
Rectangular Box (RPP) Problem Template.

A rectangular parallelepiped filled with UF6, surrounded by a wall and reflector.
Used for modeling chemical traps, HEPA filters, and rectangular GEVS components.

Geometry:
    - Inner box: UF6 (fissile material) with dimensions L × W × H
    - Wall: Steel or aluminum container (6 faces)
    - Reflector: Water, concrete, or air surrounding the box
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class RectangularBoxTemplate(ProblemTemplate):
    """
    Rectangular box (RPP) with fissile material, wall, and reflector.

    Coordinate system:
        - Origin at center of box (XY) and bottom of internal cavity (Z=0)
        - X: length direction
        - Y: width direction
        - Z: height direction (vertical)
    """

    PARAMETERS = {
        # Fissile material
        "enrichment": ParameterSpec(
            type="float",
            default=5.0,
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
            max=1.0,
            description="Fill fraction (1.0 = full)",
        ),
        # Box dimensions (internal cavity)
        "length_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=200.0,
            unit="cm",
            description="Internal length (X direction)",
        ),
        "width_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=200.0,
            unit="cm",
            description="Internal width (Y direction)",
        ),
        "height_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=200.0,
            unit="cm",
            description="Internal height (Z direction)",
        ),
        # Wall
        "wall_material": ParameterSpec(
            type="enum",
            options=["steel", "aluminum", "ss304"],
            default="steel",
            description="Container wall material",
        ),
        "wall_thickness_cm": ParameterSpec(
            type="float",
            default=0.3175,  # 1/8 inch
            min=0.0,
            max=5.0,
            unit="cm",
            description="Wall thickness (all 6 faces)",
        ),
        # Environment
        "environment_material": ParameterSpec(
            type="enum",
            options=["water", "concrete", "air", "none"],
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
            description="Reflector thickness (all sides)",
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
        Compute geometry parameters from user inputs.

        Coordinate system:
        - Box centered at (0, 0) in XY plane
        - Bottom of internal cavity at Z=0
        - Wall extends below Z=0 by wall_thickness

        Layers (inside to outside):
        1. Fissile region
        2. Wall (6 faces)
        3. Reflector (optional)
        """
        from critbuddy.core.materials import get_density

        # Internal dimensions
        length = p["length_cm"]
        width = p["width_cm"]
        height = p["height_cm"]
        wall_t = p["wall_thickness_cm"]
        fill_fraction = p.get("fill_fraction", 1.0)

        # Environment/Reflector
        environment_material = p.get("environment_material", "water")
        environment_density = p.get("environment_density")
        refl_t = p["reflector_thickness_cm"]
        if environment_material == "none":
            refl_t = 0.0

        # X coordinates (centered at 0)
        x_inner = length / 2
        x_wall = x_inner + wall_t
        x_refl = x_wall + refl_t

        # Y coordinates (centered at 0)
        y_inner = width / 2
        y_wall = y_inner + wall_t
        y_refl = y_wall + refl_t

        # Z coordinates (bottom of fissile at Z=0, wall below)
        z_fissile_bottom = 0.0
        z_fissile_top = height * fill_fraction
        z_wall_bottom = -wall_t
        z_wall_top = height + wall_t
        z_refl_bottom = z_wall_bottom - refl_t
        z_refl_top = z_wall_top + refl_t

        # Source position (center of fissile region)
        ksrc_x = 0.0
        ksrc_y = 0.0
        ksrc_z = z_fissile_top / 2

        # Material densities
        wall_density = get_density(p["wall_material"])
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

        # Total bounding box dimensions
        total_x = 2 * x_refl
        total_y = 2 * y_refl
        total_z = z_refl_top - z_refl_bottom

        return {
            # Fissile material
            "ENRICHMENT": p["enrichment"],
            "FISSILE_MATERIAL": fissile_material,
            "FISSILE_DENSITY": fissile_density,
            "H_TO_U": h_to_u,
            "FILL_FRACTION": fill_fraction,

            # Internal dimensions
            "LENGTH": length,
            "WIDTH": width,
            "HEIGHT": height,

            # X bounds (half-widths from center)
            "X_INNER": x_inner,
            "X_WALL": x_wall,
            "X_REFL": x_refl,

            # Y bounds (half-widths from center)
            "Y_INNER": y_inner,
            "Y_WALL": y_wall,
            "Y_REFL": y_refl,

            # Z bounds
            "Z_FISSILE_BOTTOM": z_fissile_bottom,
            "Z_FISSILE_TOP": z_fissile_top,
            "Z_WALL_BOTTOM": z_wall_bottom,
            "Z_WALL_TOP": z_wall_top,
            "Z_REFL_BOTTOM": z_refl_bottom,
            "Z_REFL_TOP": z_refl_top,

            # Wall
            "WALL_MATERIAL": p["wall_material"],
            "WALL_THICKNESS": wall_t,
            "WALL_DENSITY": wall_density,

            # Environment
            "ENVIRONMENT_MATERIAL": environment_material,
            "ENV_DENSITY": env_density,
            "REFL_THICKNESS": refl_t,

            # Total bounding box
            "TOTAL_X": total_x,
            "TOTAL_Y": total_y,
            "TOTAL_Z": total_z,

            # Source
            "KSRC_X": ksrc_x,
            "KSRC_Y": ksrc_y,
            "KSRC_Z": ksrc_z,
        }

    def get_plot_spec(self, dims: dict):
        """Custom PlotSpec for rectangular box visualization."""
        from critbuddy.reporting.plot_spec import PlotSpec

        total_x = dims["total_x"]
        total_y = dims["total_y"]
        total_z = dims["total_z"]
        height = dims["height"]
        wall_t = dims["wall_thickness"]
        refl_t = dims["refl_thickness"]

        # Z center accounts for wall and reflector below Z=0
        z_bottom = -wall_t - refl_t
        z_top = height + wall_t + refl_t
        z_center = (z_bottom + z_top) / 2

        center = (0.0, 0.0, z_center)

        padding = 1.1
        width = (total_x * padding, total_y * padding, total_z * padding)

        return PlotSpec(
            center=center,
            width=width,
            up_axis="z",
            exclude_materials=["Air", "Water"],  # Hide environment for cleaner visualization
        )


# Export the template class
Template = RectangularBoxTemplate
