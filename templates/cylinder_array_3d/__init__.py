"""
3D Cylinder Array Problem Template.

A 3D array of vertical cylinders filled with UF6, arranged in rows x cols x layers.
Used for studying interaction effects in stacked storage configurations.

Geometry:
    - Cylinders arranged in a 3D grid (rows × cols × layers)
    - X: rows direction
    - Y: cols direction
    - Z: layers direction (stacked vertically)
    - Each cylinder: UF6 core with steel wall and end caps
    - Water environment surrounding all cylinders
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CylinderArray3DTemplate(ProblemTemplate):
    """
    3D array of vertical cylinders with fissile material.

    Coordinate system:
        - X: row direction (up to 150 rows)
        - Y: column direction (up to 10 cols)
        - Z: layer direction (stacked, up to 10 layers)
        - Origin at center of array
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
            max=150,
            description="Number of rows (X direction)",
        ),
        "cols": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=10,
            description="Number of columns (Y direction)",
        ),
        "layers": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=10,
            description="Number of stacked layers (Z direction)",
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
            description="Cylinder height (UF6 region)",
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
        "gap_xy_cm": ParameterSpec(
            type="float",
            required=True,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Horizontal gap between cylinder outer walls (X and Y)",
        ),
        "gap_z_cm": ParameterSpec(
            type="float",
            required=True,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Vertical gap between stacked layers",
        ),
        "fissile_material": ParameterSpec(
            type="enum",
            options=["uf6", "uo2f2"],
            default="uf6",
            description="Fissile material type (uf6 or uo2f2)",
        ),
        "fissile_density": ParameterSpec(
            type="float",
            default=5.09,
            min=1.0,
            max=7.0,
            unit="g/cc",
            description="Fissile material density (UF6: 5.09, UO2F2: 6.37)",
        ),
        "h_to_u_ratio": ParameterSpec(
            type="float",
            required=False,
            default=0.0,
            min=0.0,
            max=500.0,
            unit="",
            description="H/U atomic ratio for wet UO2F2 (0 = dry, higher = more water)",
        ),
        "environment_material": ParameterSpec(
            type="enum",
            options=["humid_air", "air"],
            default="humid_air",
            description="Material between units and surrounding array",
        ),
        "void_material": ParameterSpec(
            type="enum",
            options=["void", "air", "humid_air"],
            default="void",
            description="Material in headspace above partial fill",
        ),
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=5.0,
            max=100.0,
            unit="cm",
            description="Reflector thickness around array",
        ),
        "fill_fraction": ParameterSpec(
            type="float",
            default=1.0,
            min=0.01,
            max=1.0,
            description="Fill fraction (1.0 = 100%, 0.01 = 1%)",
        ),
        "boundary_type": ParameterSpec(
            type="enum",
            options=["vacuum", "reflective"],
            default="vacuum",
            description="Boundary condition type (vacuum=finite, reflective=infinite array)",
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
        layers = p["layers"]
        radius = p["radius_cm"]
        wall = p["wall_thickness_cm"]
        gap_xy = p["gap_xy_cm"]
        gap_z = p["gap_z_cm"]
        height = p["height_cm"]
        reflector_thickness = p["reflector_thickness_cm"]
        fill_fraction = p.get("fill_fraction", 1.0)

        # Material selections
        fissile_material = p["fissile_material"]
        fissile_density = p["fissile_density"]
        h_to_u_ratio = p.get("h_to_u_ratio", 0.0)
        environment_material = p["environment_material"]
        void_material = p["void_material"]

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
            # Materials
            "ENRICHMENT": p["enrichment"],
            "FISSILE_MATERIAL": fissile_material,
            "FISSILE_DENSITY": fissile_density,
            "H_TO_U_RATIO": h_to_u_ratio,
            "WALL_MATERIAL": p["wall_material"],
            "WALL_DENSITY": wall_density,
            "ENVIRONMENT_MATERIAL": environment_material,
            "VOID_MATERIAL": void_material,
            # Fill fraction
            "FILL_FRACTION": fill_fraction,
            "FISSILE_HEIGHT": uf6_height,  # Actual fissile height (height * fill_fraction)
            # Boundary condition
            "BOUNDARY_TYPE": p.get("boundary_type", "vacuum"),
        }


# Export the template class
Template = CylinderArray3DTemplate
