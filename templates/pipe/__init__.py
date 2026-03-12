"""
Pipe Template.

Unified template for single or arrayed horizontal pipes, filled with UF6 or UO2F2.
Supports standard NPS pipe sizes per ASME B36.10M Schedule 10/10S.

Geometry:
    - Horizontal cylinders along X-axis
    - Single pipe (rows=1, cols=1) or 2D array (rows x cols)
    - Pipes arranged along Y-axis (side by side) and Z-axis (stacked rows)
    - Wall: SS304 or carbon steel
    - Reflector: Water surrounding the pipes
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class PipeTemplate(ProblemTemplate):
    """
    Unified template for single or arrayed horizontal pipes.

    Coordinate system:
        - X: pipe length direction (horizontal)
        - Y: pipe arrangement direction (side by side)
        - Z: vertical (stacked rows)
        - Origin at center of pipe array
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
            description="Fill fraction by HEIGHT (0=empty, 0.5=half, 1.0=full). Note: not volume fraction.",
        ),
        # Array configuration
        "rows": ParameterSpec(
            type="int",
            default=1,
            min=1,
            max=10,
            description="Number of rows (Z-direction, vertical stacking)",
        ),
        "cols": ParameterSpec(
            type="int",
            default=1,
            min=1,
            max=10,
            description="Number of pipes per row (Y-direction)",
        ),
        "gap_cm": ParameterSpec(
            type="float",
            default=5.0,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Edge-to-edge gap between pipes",
        ),
        # Pipe geometry
        "pipe_size": ParameterSpec(
            type="enum",
            options=["1/8", "1/4", "3/8", "1", "1-1/4", "1-1/2", "2", "2-1/2",
                     "3", "3-1/2", "4", "5", "6", "8", "custom"],
            default="2",
            description="NPS pipe size (Schedule 10/10S) or 'custom'",
        ),
        "radius_cm": ParameterSpec(
            type="float",
            default=None,
            min=0.1,
            max=50.0,
            unit="cm",
            description="Inner radius (only for custom pipe)",
        ),
        "wall_thickness_cm": ParameterSpec(
            type="float",
            default=None,
            min=0.05,
            max=5.0,
            unit="cm",
            description="Wall thickness (only for custom pipe)",
        ),
        "length_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=1000.0,
            unit="cm",
            description="Pipe length",
        ),
        # Wall
        "wall_material": ParameterSpec(
            type="enum",
            options=["ss304", "steel", "aluminum"],
            default="ss304",
            description="Pipe wall material",
        ),
        # Environment
        "environment_material": ParameterSpec(
            type="enum",
            options=["humid_air", "air", "water"],
            default="humid_air",
            description="Environment material around pipes",
        ),
        "environment_density": ParameterSpec(
            type="float",
            default=None,
            min=0.00001,
            max=2.0,
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
        """Compute geometry parameters from user inputs."""
        from critbuddy.core.pipes import get_pipe
        from critbuddy.core.materials import get_density

        # Array dimensions (default to single pipe)
        cols = int(p.get("cols", 1))
        rows = int(p.get("rows", 1))

        # Get pipe dimensions
        if p["pipe_size"] == "custom":
            r_inner = p.get("radius_cm", p.get("inner_radius_cm"))
            wall_t = p["wall_thickness_cm"]
            if r_inner is None or wall_t is None:
                raise ValueError("Custom pipe requires radius_cm and wall_thickness_cm")
        else:
            pipe = get_pipe(p["pipe_size"])
            r_inner = pipe.inner_radius_cm
            wall_t = pipe.wall_thickness_cm

        r_outer = r_inner + wall_t
        length = p["length_cm"]
        gap = p["gap_cm"]

        # Pitch (center-to-center distance) - same in Y and Z for equidistant
        pitch = 2 * r_outer + gap

        # Calculate pipe center positions along Y axis (centered)
        pipe_y_positions = []
        for i in range(cols):
            y = (i - (cols - 1) / 2) * pitch
            pipe_y_positions.append(y)

        # Calculate pipe center positions along Z axis (centered)
        pipe_z_positions = []
        for i in range(rows):
            z = (i - (rows - 1) / 2) * pitch
            pipe_z_positions.append(z)

        # Reflector thickness
        reflector_t = p["reflector_thickness_cm"]

        # Array extents
        y_extent = max(abs(y) for y in pipe_y_positions) + r_outer if pipe_y_positions else r_outer
        y_total = y_extent + reflector_t

        z_extent = max(abs(z) for z in pipe_z_positions) + r_outer if pipe_z_positions else r_outer
        z_total = z_extent + reflector_t

        # X boundaries
        x_inner = length / 2
        x_total = x_inner + reflector_t

        # Material densities
        wall_density = get_density(p["wall_material"])

        environment_material = p.get("environment_material", "humid_air")
        environment_density = p.get("environment_density")
        if environment_density is not None:
            env_density = environment_density
        else:
            env_density = get_density(environment_material)

        # Fissile material properties
        fissile_material = p.get("fissile_material", "uf6")
        fissile_density = p.get("fissile_density")
        h_to_u = p.get("h_to_u", 0.0)

        # Fill fraction (for partial fill)
        fill_fraction = p.get("fill_fraction", 1.0)
        # Height-based fill: fill_fraction maps linearly to z-coordinate
        # 0.0 = empty (z = -r), 0.5 = half height (z = 0), 1.0 = full (z = +r)
        # Note: This is HEIGHT fraction, not volume fraction.
        # At 50% height, volume is 50%. At 25% height, volume is ~20%.
        fill_height = (fill_fraction * 2 - 1) * r_inner

        # Total bounding box
        total_x = 2 * x_total
        total_y = 2 * y_total
        total_z = 2 * z_total

        # Total pipe count
        total_pipes = cols * rows

        return {
            # Fissile material
            "ENRICHMENT": p["enrichment"],
            "FISSILE_MATERIAL": fissile_material,
            "FISSILE_DENSITY": fissile_density,
            "H_TO_U": h_to_u,
            "FILL_FRACTION": fill_fraction,
            "FILL_HEIGHT": fill_height,

            # Array dimensions
            "ROWS": rows,
            "COLS": cols,
            "TOTAL_PIPES": total_pipes,

            # Pipe geometry
            "PIPE_SIZE": p["pipe_size"],
            "R_INNER": r_inner,
            "R_OUTER": r_outer,
            "LENGTH": length,
            "WALL_THICKNESS": wall_t,
            "GAP": gap,
            "PITCH": pitch,

            # Pipe positions (2D grid)
            "PIPE_Y_POSITIONS": pipe_y_positions,
            "PIPE_Z_POSITIONS": pipe_z_positions,

            # Boundaries
            "X_INNER": x_inner,
            "X_TOTAL": x_total,
            "Y_EXTENT": y_extent,
            "Y_TOTAL": y_total,
            "Z_EXTENT": z_extent,
            "Z_TOTAL": z_total,

            # Wall
            "WALL_MATERIAL": p["wall_material"],
            "WALL_DENSITY": wall_density,

            # Environment
            "ENVIRONMENT_MATERIAL": environment_material,
            "ENV_DENSITY": env_density,
            "REFLECTOR_THICKNESS": reflector_t,

            # Bounding box
            "TOTAL_X": total_x,
            "TOTAL_Y": total_y,
            "TOTAL_Z": total_z,

            # Source position (center of array)
            "KSRC_X": 0.0,
            "KSRC_Y": 0.0,
            "KSRC_Z": 0.0,
        }

    def get_plot_spec(self, dims: dict):
        """Provide custom PlotSpec for 3D visualization."""
        from critbuddy.reporting.plot_spec import PlotSpec

        # Exclude environment materials from voxel plot
        environment = dims.get("environment", "humid_air")
        if environment == "water":
            env_name = "Water"
        elif environment == "air":
            env_name = "Air"
        else:  # humid_air
            env_name = "Humid_Air"

        # Higher resolution for cylindrical geometry (need ~15 voxels per pipe diameter)
        pipe_diameter = 2 * dims.get("r_outer", 5.0)
        min_cross_section = min(dims["total_y"], dims["total_z"])
        target_resolution = int(min_cross_section / pipe_diameter * 15)
        max_res = max(200, min(target_resolution, 300))  # Clamp between 200-300

        return PlotSpec(
            center=(0.0, 0.0, 0.0),
            width=(dims["total_x"], dims["total_y"], dims["total_z"]),
            exclude_materials=[env_name, "Humid_Air", "Water", "Air", "Vacuum"],
            max_resolution=max_res,
        )


# Export the template class
Template = PipeTemplate
