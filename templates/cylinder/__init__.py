"""
Unified Cylinder Problem Template.

A single cylinder or 3D array of vertical cylinders filled with UF6.
Supports single cylinders (rows=cols=layers=1) or arrays with configurable spacing.

Geometry:
    - Single cylinder or grid arrangement (rows x cols x layers)
    - X: rows direction
    - Y: cols direction
    - Z: layers direction (stacked vertically)
    - Each cylinder: UF6 core with steel wall and end caps
    - Configurable environment material surrounding cylinders
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CylinderTemplate(ProblemTemplate):
    """
    Unified template for single or arrayed vertical cylinders with fissile material.

    Supports:
        - Single cylinder (default: rows=cols=layers=1)
        - 2D array (rows x cols, single layer)
        - 3D array (rows x cols x layers)

    Coordinate system:
        - X: row direction (up to 150 rows)
        - Y: column direction (up to 10 cols)
        - Z: layer direction (stacked, up to 10 layers)
        - Origin at center of array
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
            default=5.09,
            min=1.0,
            max=7.0,
            unit="g/cc",
            description="Fissile material density (UF6: 5.09, UO2F2: 6.37)",
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
        # Array configuration (all default to 1 for single cylinder)
        "rows": ParameterSpec(
            type="int",
            default=1,
            min=1,
            max=150,
            description="Number of rows (X direction)",
        ),
        "cols": ParameterSpec(
            type="int",
            default=1,
            min=1,
            max=10,
            description="Number of columns (Y direction)",
        ),
        "layers": ParameterSpec(
            type="int",
            default=1,
            min=1,
            max=10,
            description="Number of stacked layers (Z direction)",
        ),
        "gap_cm": ParameterSpec(
            type="float",
            default=None,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Uniform gap between cylinders (applies to both horizontal and vertical)",
        ),
        "gap_horizontal_cm": ParameterSpec(
            type="float",
            default=0.0,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Horizontal gap between cylinder outer walls (X and Y)",
        ),
        "gap_vertical_cm": ParameterSpec(
            type="float",
            default=0.0,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Vertical gap between stacked layers",
        ),
        # Cylinder geometry
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
        # Wall
        "wall_material": ParameterSpec(
            type="enum",
            options=["aluminum", "steel", "ss304", "monel"],
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
        # Environment
        "environment": ParameterSpec(
            type="enum",
            options=["humid_air", "air", "water"],
            default="humid_air",
            description="Environment material around array",
        ),
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=5.0,
            max=100.0,
            unit="cm",
            description="Reflector thickness around array",
        ),
        "void_material": ParameterSpec(
            type="enum",
            options=["void", "air", "humid_air"],
            default="void",
            description="Material in headspace above partial fill",
        ),
        "boundary_type": ParameterSpec(
            type="enum",
            options=["vacuum", "reflective"],
            default="vacuum",
            description="Boundary condition (vacuum=finite, reflective=infinite)",
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

        rows = p.get("rows", 1)
        cols = p.get("cols", 1)
        layers = p.get("layers", 1)
        radius = p["radius_cm"]
        wall = p["wall_thickness_cm"]

        # Handle gap_cm as shorthand for both horizontal and vertical gaps
        uniform_gap = p.get("gap_cm")
        if uniform_gap is not None:
            gap_xy = uniform_gap
            gap_z = uniform_gap
        else:
            gap_xy = p.get("gap_horizontal_cm", p.get("gap_xy_cm", 0.0))
            gap_z = p.get("gap_vertical_cm", p.get("gap_z_cm", 0.0))
        height = p["height_cm"]
        reflector_thickness = p["reflector_thickness_cm"]
        fill_fraction = p.get("fill_fraction", 1.0)

        # Material selections
        fissile_material = p.get("fissile_material", "uf6")
        fissile_density = p.get("fissile_density", 5.09)
        h_to_u = p.get("h_to_u", 0.0)
        environment = p.get("environment", "humid_air")
        void_material = p.get("void_material", "void")

        # Apply fill fraction to UF6 height
        uf6_height = height * fill_fraction

        # Outer radius of each cylinder (with wall)
        outer_radius = radius + wall

        # Total height of one cylinder (UF6 + top/bottom caps)
        total_cyl_height = height + 2 * wall

        # Spacing (center-to-center, derived from gap)
        spacing_xy = gap_xy + 2 * outer_radius  # Horizontal (X and Y)
        spacing_z = gap_z + total_cyl_height     # Vertical (Z)

        # Array dimensions (from outermost walls)
        array_x = (rows - 1) * spacing_xy + 2 * outer_radius
        array_y = (cols - 1) * spacing_xy + 2 * outer_radius
        array_z = (layers - 1) * spacing_z + total_cyl_height

        # Total bounding box (including reflector)
        total_x = array_x + 2 * reflector_thickness
        total_y = array_y + 2 * reflector_thickness
        total_z = array_z + 2 * reflector_thickness

        # Offsets to center array at origin
        x_offset = -(rows - 1) * spacing_xy / 2
        y_offset = -(cols - 1) * spacing_xy / 2
        z_offset = -(layers - 1) * spacing_z / 2

        # Material densities
        wall_density = get_density(p["wall_material"])
        water_density = p.get("water_density", 1.0)

        return {
            # Array configuration
            "ROWS": rows,
            "COLS": cols,
            "LAYERS": layers,
            "TOTAL_CYLINDERS": rows * cols * layers,
            # Spacing (gap = wall-to-wall distance)
            "GAP_XY": gap_xy,
            "GAP_Z": gap_z,
            "SPACING_XY": spacing_xy,  # center-to-center = gap + 2*outer_radius
            "SPACING_Z": spacing_z,    # center-to-center = gap + total_cyl_height
            # Cylinder geometry
            "INNER_RADIUS": radius,
            "OUTER_RADIUS": outer_radius,
            "HEIGHT": height,
            "WALL_THICKNESS": wall,
            "TOTAL_CYL_HEIGHT": total_cyl_height,
            # Offsets for centering
            "X_OFFSET": x_offset,
            "Y_OFFSET": y_offset,
            "Z_OFFSET": z_offset,
            # Bounding box
            "ARRAY_X": array_x,
            "ARRAY_Y": array_y,
            "ARRAY_Z": array_z,
            "TOTAL_X": total_x,
            "TOTAL_Y": total_y,
            "TOTAL_Z": total_z,
            "REFLECTOR_THICKNESS": reflector_thickness,
            # Source position (center of array)
            "KSRC_X": 0.0,
            "KSRC_Y": 0.0,
            "KSRC_Z": 0.0,
            # Fissile material
            "ENRICHMENT": p["enrichment"],
            "FISSILE_MATERIAL": fissile_material,
            "FISSILE_DENSITY": fissile_density,
            "H_TO_U": h_to_u,
            # Wall
            "WALL_MATERIAL": p["wall_material"],
            "WALL_DENSITY": wall_density,
            # Environment
            "ENVIRONMENT": environment,
            "VOID_MATERIAL": void_material,
            # Fill fraction
            "FILL_FRACTION": fill_fraction,
            "FISSILE_HEIGHT": uf6_height,  # Actual fissile height (height * fill_fraction)
            # Boundary condition
            "BOUNDARY_TYPE": p.get("boundary_type", "vacuum"),
        }


# Export the template class
Template = CylinderTemplate
