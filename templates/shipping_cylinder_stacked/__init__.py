"""
Shipping Cylinder Stacked Template.

Horizontal UF6 shipping cylinders stacked in pyramid or rectangular configurations.
Uses ANSI N14.1 cylinder registry for standard dimensions (30B, 48Y, etc.).

Geometry:
    - Cylinders lying horizontal (axis along X direction)
    - Stacking patterns: pyramid (3,2,1), rectangular (3,3,3), etc.
    - Floor/pad below bottom layer
    - Surrounding environment (air or water for flooding)

Use cases:
    - Stacked shipping cylinders in warehouses
    - Pyramid storage configurations (3-2-1, 2-1, etc.)
    - Flooding scenarios for safety analysis
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec
from critbuddy.core.cylinders import CYLINDER_REGISTRY


class ShippingCylinderStackedTemplate(ProblemTemplate):
    """
    Stacked horizontal UF6 shipping cylinders with pyramid support.

    Coordinate system:
        - X: cylinder length direction (horizontal)
        - Y: side-by-side arrangement within each layer
        - Z: vertical stacking direction
        - Origin at center of array (XY) and floor surface (Z=0)
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
        # Stacking configuration
        "stacking_pattern": ParameterSpec(
            type="string",
            required=True,
            description="Comma-separated cylinders per layer from bottom, e.g. '3,2,1' for pyramid or '3,3,3' for rectangular",
        ),

        # Spacing
        "gap_y_cm": ParameterSpec(
            type="float",
            default=0.0,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Edge-to-edge gap between cylinders in Y direction (same layer)",
        ),
        "gap_z_cm": ParameterSpec(
            type="float",
            default=0.0,
            min=0.0,
            max=50.0,
            unit="cm",
            description="Gap between layers (top of lower to bottom of upper)",
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
            description="Floor thickness",
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
        Compute geometry parameters from user inputs.

        The stacking_pattern defines how many cylinders are in each layer,
        from bottom to top. For example:
        - "3,2,1" = pyramid with 3 on bottom, 2 in middle, 1 on top
        - "3,3,3" = rectangular 3-high stack
        - "2,1" = simple 2-layer pyramid
        """
        from critbuddy.core.cylinders import get_cylinder, get_inner_radius
        from critbuddy.core.materials import get_density

        # Parse stacking pattern
        pattern_str = p["stacking_pattern"].strip()
        layers_count = [int(x.strip()) for x in pattern_str.split(",")]
        num_layers = len(layers_count)
        max_per_layer = max(layers_count)

        # Get cylinder specs from registry
        spec = get_cylinder(p["cylinder_type"])
        r_inner = get_inner_radius(p["cylinder_type"])
        wall_t = spec.wall_thickness_cm
        wall_material = spec.wall_material
        cyl_internal_height = spec.internal_height_cm  # This is the length when horizontal

        # Cylinder dimensions when lying horizontal:
        # - Radius is the same
        # - "Length" along X axis is the internal_height + 2*wall_t
        r_outer = r_inner + wall_t
        cyl_diameter = 2 * r_outer
        cyl_length = cyl_internal_height + 2 * wall_t

        gap_y = p["gap_y_cm"]
        gap_z = p["gap_z_cm"]
        boundary = p["boundary_thickness_cm"]

        # Pitch (center-to-center in Y direction)
        pitch_y = cyl_diameter + gap_y
        pitch_z = cyl_diameter + gap_z

        # Calculate cylinder positions
        # Each layer is centered in Y, with cylinders distributed evenly
        cylinder_positions = []  # List of (layer_idx, y_position, z_position)

        for layer_idx, count in enumerate(layers_count):
            # Z position: center of cylinder for this layer
            # Cylinders sit on floor (Z=0), so first layer center is at Z=r_outer
            z_center = r_outer + layer_idx * pitch_z

            # Y positions: centered, evenly spaced
            if count == 1:
                y_positions = [0.0]
            else:
                y_start = -((count - 1) * pitch_y) / 2
                y_positions = [y_start + i * pitch_y for i in range(count)]

            for y_pos in y_positions:
                cylinder_positions.append({
                    "layer": layer_idx,
                    "y": y_pos,
                    "z": z_center,
                })

        total_cylinders = len(cylinder_positions)

        # Array extents
        array_y = (max_per_layer - 1) * pitch_y + cyl_diameter if max_per_layer > 0 else cyl_diameter
        array_z = num_layers * cyl_diameter + (num_layers - 1) * gap_z
        array_x = cyl_length  # Single row of cylinders in X

        # Total bounding box
        total_x = array_x + 2 * boundary
        total_y = array_y + 2 * boundary
        total_z = array_z + boundary  # Floor below, boundary above

        # Floor parameters
        floor_t = p["floor_thickness_cm"]
        if p["floor_material"] == "none":
            floor_t = 0.0

        # Z coordinates
        z_floor_bottom = -floor_t
        z_floor_top = 0.0
        z_array_top = array_z
        z_env_top = array_z + boundary

        # X boundaries (all cylinders same length, centered at X=0)
        x_half = cyl_length / 2
        x_inner_half = cyl_internal_height / 2  # UF6 region

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

            # Cylinder geometry (horizontal orientation)
            "R_INNER": r_inner,
            "R_OUTER": r_outer,
            "CYL_LENGTH": cyl_length,
            "CYL_INTERNAL_LENGTH": cyl_internal_height,  # UF6 region length
            "WALL_THICKNESS": wall_t,
            "WALL_MATERIAL": wall_material,
            "WALL_DENSITY": wall_density,

            # Stacking configuration
            "STACKING_PATTERN": pattern_str,
            "LAYERS_COUNT": layers_count,
            "NUM_LAYERS": num_layers,
            "MAX_PER_LAYER": max_per_layer,
            "TOTAL_CYLINDERS": total_cylinders,
            "CYLINDER_POSITIONS": cylinder_positions,

            # Spacing
            "GAP_Y": gap_y,
            "GAP_Z": gap_z,
            "PITCH_Y": pitch_y,
            "PITCH_Z": pitch_z,

            # X boundaries
            "X_HALF": x_half,
            "X_INNER_HALF": x_inner_half,

            # Array extents
            "ARRAY_X": array_x,
            "ARRAY_Y": array_y,
            "ARRAY_Z": array_z,

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
            "Z_ARRAY_TOP": z_array_top,
            "Z_ENV_TOP": z_env_top,

            # Environment
            "ENVIRONMENT": p["environment"],
            "ENV_DENSITY": env_density,

            # Source (center of middle cylinder)
            "KSRC_X": 0.0,
            "KSRC_Y": 0.0,
            "KSRC_Z": array_z / 2,
        }


# Export the template class
Template = ShippingCylinderStackedTemplate
