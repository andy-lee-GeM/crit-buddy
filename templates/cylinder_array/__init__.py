"""
Cylinder Array Problem Template.

An array of vertical cylinders filled with UF6, surrounded by an environment.
Used for studying interaction effects between multiple fissile units.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CylinderArrayTemplate(ProblemTemplate):
    """
    Rectangular array of vertical cylinders with fissile material.

    Geometry:
        - Multiple cylinders arranged in rows x cols grid
        - Each cylinder: UF6 core with steel wall
        - Configurable gap between outer walls of adjacent cylinders
        - Surrounding environment: air or water
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
        "rows": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=10,
            description="Number of rows in array",
        ),
        "cols": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=10,
            description="Number of columns in array",
        ),
        "radius_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=50.0,
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
            default="steel",
            description="Container wall material",
        ),
        "wall_thickness_cm": ParameterSpec(
            type="float",
            default=0.6,
            min=0.0,
            max=5.0,
            unit="cm",
            description="Wall thickness",
        ),
        "gap_cm": ParameterSpec(
            type="float",
            required=True,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Gap between outer walls of adjacent cylinders",
        ),
        "water_density": ParameterSpec(
            type="float",
            default=1.0,
            min=0.001,
            max=1.0,
            unit="g/cc",
            description="Water density (0.001=mist, 1.0=flooded)",
        ),
        "water_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=5.0,
            max=100.0,
            unit="cm",
            description="Water thickness around array",
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
        Compute geometry parameters from user inputs.
        """
        from critbuddy.core.materials import get_density

        rows = p["rows"]
        cols = p["cols"]
        radius = p["radius_cm"]
        wall = p["wall_thickness_cm"]
        gap = p["gap_cm"]  # Gap between outer walls
        height = p["height_cm"]
        water_thickness = p["water_thickness_cm"]

        # Outer radius of each cylinder (with wall)
        outer_radius = radius + wall

        # Center-to-center spacing = gap + 2 * outer_radius
        center_to_center = gap + 2 * outer_radius

        # Array dimensions (from leftmost outer wall to rightmost outer wall)
        array_width_x = (cols - 1) * center_to_center + 2 * outer_radius
        array_width_y = (rows - 1) * center_to_center + 2 * outer_radius

        # Total bounding box (including water)
        total_x = array_width_x + 2 * water_thickness
        total_y = array_width_y + 2 * water_thickness
        total_z = height + 2 * water_thickness

        # Array center offset (so cylinders are centered)
        x_offset = -(cols - 1) * center_to_center / 2
        y_offset = -(rows - 1) * center_to_center / 2

        # Material densities
        wall_density = get_density(p["wall_material"])
        water_density = p.get("water_density", 1.0)

        return {
            # Array configuration
            "ROWS": rows,
            "COLS": cols,
            "PITCH": center_to_center,  # Center-to-center for model positioning
            "GAP": gap,  # Original gap between outer walls
            # Cylinder geometry
            "INNER_RADIUS": radius,
            "OUTER_RADIUS": outer_radius,
            "HEIGHT": height,
            "WALL_THICKNESS": wall,
            # Offsets for centering
            "X_OFFSET": x_offset,
            "Y_OFFSET": y_offset,
            # Bounding box
            "TOTAL_X": total_x,
            "TOTAL_Y": total_y,
            "TOTAL_Z": total_z,
            "WATER_THICKNESS": water_thickness,
            # Z coordinates (caps extend wall thickness above/below UF6)
            "Z_BOTTOM": 0.0,
            "Z_TOP": height,
            "Z_CAP_BOTTOM": -wall,
            "Z_CAP_TOP": height + wall,
            "Z_ENV_BOTTOM": -water_thickness,
            "Z_ENV_TOP": height + water_thickness,
            # Source position
            "KSRC_Z": height / 2.0,
            # Materials
            "ENRICHMENT": p["enrichment"],
            "UF6_DENSITY": p["uf6_density"],
            "WALL_MATERIAL": p["wall_material"],
            "WALL_DENSITY": wall_density,
            "WATER_DENSITY": water_density,
        }


# Export the template class
Template = CylinderArrayTemplate
