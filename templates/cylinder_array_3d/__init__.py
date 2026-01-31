"""
3D Cylinder Array Problem Template.

A three-dimensional array of UF6 shipping cylinders arranged in rows × cols × layers.
Uses the cylinder registry for standard shipping cylinder dimensions (30B, 48Y, etc.).
Includes floor/pad modeling for realistic warehouse storage scenarios.

Use cases:
- Stacked shipping cylinders (2-high, 3-high)
- Arrays of stacked cylinders in warehouse storage
- Interaction studies for storage configurations
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec
from critbuddy.core.cylinders import CYLINDER_REGISTRY


class CylinderArray3DTemplate(ProblemTemplate):
    """
    3D array of UF6 shipping cylinders with floor modeling.

    Geometry:
        - Cylinders arranged in rows × cols × layers grid
        - Cylinder dimensions from registry (30B, 48Y, etc.)
        - Configurable gaps in X, Y, and Z directions
        - Floor/pad below bottom layer
        - Surrounding environment (air or water for flooding)
    """

    PARAMETERS = {
        # Cylinder specification
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

        # Array configuration
        "rows": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=10,
            description="Number of rows (Y direction)",
        ),
        "cols": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=10,
            description="Number of columns (X direction)",
        ),
        "layers": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=5,
            description="Number of vertical layers (Z direction, stack height)",
        ),

        # Spacing
        "gap_x_cm": ParameterSpec(
            type="float",
            default=10.0,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Gap between outer walls in X direction",
        ),
        "gap_y_cm": ParameterSpec(
            type="float",
            default=10.0,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Gap between outer walls in Y direction",
        ),
        "gap_z_cm": ParameterSpec(
            type="float",
            default=5.0,
            min=0.0,
            max=50.0,
            unit="cm",
            description="Gap between top of lower cylinder and bottom of upper cylinder",
        ),

        # Floor
        "floor_material": ParameterSpec(
            type="enum",
            options=["concrete", "steel", "none"],
            default="concrete",
            description="Floor/pad material below the array",
        ),
        "floor_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Floor thickness (for moderation effects)",
        ),

        # Environment
        "environment": ParameterSpec(
            type="enum",
            options=["air", "water"],
            default="air",
            description="Environment material (water for flooding scenario)",
        ),
        "boundary_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=5.0,
            max=100.0,
            unit="cm",
            description="Environment thickness around and above array",
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

        Coordinate system:
        - Origin at center of array (XY) and at floor surface (Z=0)
        - Cylinders sit on floor starting at Z=0
        - Floor extends below Z=0
        """
        from critbuddy.core.cylinders import get_cylinder, get_inner_radius
        from critbuddy.core.materials import get_density

        # Get cylinder specs from registry
        spec = get_cylinder(p["cylinder_type"])
        r_inner = get_inner_radius(p["cylinder_type"])
        wall_t = spec.wall_thickness_cm
        wall_material = spec.wall_material
        cyl_internal_height = spec.internal_height_cm

        # Total cylinder height (internal + top/bottom caps)
        cyl_total_height = cyl_internal_height + 2 * wall_t
        r_outer = r_inner + wall_t

        # Array dimensions
        rows = p["rows"]
        cols = p["cols"]
        layers = p["layers"]
        gap_x = p["gap_x_cm"]
        gap_y = p["gap_y_cm"]
        gap_z = p["gap_z_cm"]
        boundary = p["boundary_thickness_cm"]

        # Center-to-center spacing
        pitch_x = gap_x + 2 * r_outer
        pitch_y = gap_y + 2 * r_outer
        pitch_z = cyl_total_height + gap_z

        # Array extents (outer walls of cylinders)
        array_x = (cols - 1) * pitch_x + 2 * r_outer
        array_y = (rows - 1) * pitch_y + 2 * r_outer
        array_z = layers * cyl_total_height + (layers - 1) * gap_z

        # Total bounding box (including environment)
        total_x = array_x + 2 * boundary
        total_y = array_y + 2 * boundary
        total_z = array_z + boundary  # Only boundary above, floor below

        # Offsets for centering array in XY plane
        x_offset = -(cols - 1) * pitch_x / 2
        y_offset = -(rows - 1) * pitch_y / 2

        # Floor parameters
        floor_t = p["floor_thickness_cm"]
        if p["floor_material"] == "none":
            floor_t = 0.0

        # Z coordinates
        # Floor surface is at Z=0, cylinders sit on top
        z_floor_bottom = -floor_t
        z_floor_top = 0.0
        z_array_bottom = 0.0
        z_array_top = array_z
        z_env_top = array_z + boundary

        # Material densities
        wall_density = get_density(wall_material)
        env_density = get_density(p["environment"])
        floor_density = get_density(p["floor_material"]) if p["floor_material"] != "none" else 0.0

        return {
            # Cylinder info
            "CYLINDER_TYPE": p["cylinder_type"].upper(),
            "CYLINDER_NAME": spec.name,
            "ENRICHMENT": p["enrichment"],
            "UF6_DENSITY": p["uf6_density"],

            # Cylinder geometry
            "R_INNER": r_inner,
            "R_OUTER": r_outer,
            "CYL_INTERNAL_HEIGHT": cyl_internal_height,
            "CYL_TOTAL_HEIGHT": cyl_total_height,
            "WALL_THICKNESS": wall_t,
            "WALL_MATERIAL": wall_material,
            "WALL_DENSITY": wall_density,

            # Array configuration
            "ROWS": rows,
            "COLS": cols,
            "LAYERS": layers,
            "GAP_X": gap_x,
            "GAP_Y": gap_y,
            "GAP_Z": gap_z,
            "PITCH_X": pitch_x,
            "PITCH_Y": pitch_y,
            "PITCH_Z": pitch_z,

            # Array extents
            "ARRAY_X": array_x,
            "ARRAY_Y": array_y,
            "ARRAY_Z": array_z,
            "X_OFFSET": x_offset,
            "Y_OFFSET": y_offset,

            # Bounding box
            "TOTAL_X": total_x,
            "TOTAL_Y": total_y,
            "TOTAL_Z": total_z,
            "BOUNDARY": boundary,

            # Floor
            "FLOOR_MATERIAL": p["floor_material"],
            "FLOOR_THICKNESS": floor_t,
            "FLOOR_DENSITY": floor_density,
            "Z_FLOOR_BOTTOM": z_floor_bottom,
            "Z_FLOOR_TOP": z_floor_top,

            # Z coordinates
            "Z_ARRAY_BOTTOM": z_array_bottom,
            "Z_ARRAY_TOP": z_array_top,
            "Z_ENV_TOP": z_env_top,

            # Environment
            "ENVIRONMENT": p["environment"],
            "ENV_DENSITY": env_density,

            # Source (center of middle layer)
            "KSRC_Z": (layers - 1) * pitch_z / 2 + cyl_total_height / 2,
        }


# Export the template class
Template = CylinderArray3DTemplate
