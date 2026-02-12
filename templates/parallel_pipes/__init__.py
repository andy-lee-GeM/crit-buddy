"""
Parallel Pipes Template.

1-3 horizontal pipes running side by side, filled with UF6.
Supports standard NPS pipe sizes per ASME B36.10M Schedule 10/10S.

Geometry:
    - Horizontal cylinders along X-axis
    - Pipes arranged along Y-axis (side by side)
    - Wall: SS304 or carbon steel
    - Reflector: Water, concrete, or air surrounding the pipes
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class ParallelPipesTemplate(ProblemTemplate):
    """
    1-3 horizontal pipes running in parallel.

    Coordinate system:
        - X: pipe length direction (horizontal)
        - Y: pipe arrangement direction (side by side)
        - Z: vertical
        - Origin at center of pipe array
    """

    PARAMETERS = {
        # Number of pipes
        "num_pipes": ParameterSpec(
            type="int",
            default=3,
            min=1,
            max=3,
            description="Number of parallel pipes (1-3)",
        ),

        # Pipe selection
        "pipe_size": ParameterSpec(
            type="enum",
            options=["1/8", "1/4", "3/8", "1", "1-1/4", "1-1/2", "2", "2-1/2",
                     "3", "3-1/2", "4", "5", "6", "8", "custom"],
            default="2",
            description="NPS pipe size (Schedule 10/10S) or 'custom'",
        ),

        # Custom dimensions (only used if pipe_size="custom")
        "inner_radius_cm": ParameterSpec(
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

        # Pipe length and spacing
        "length_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=1000.0,
            unit="cm",
            description="Pipe length",
        ),
        "gap_cm": ParameterSpec(
            type="float",
            default=5.0,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Edge-to-edge gap between pipes",
        ),

        # Fissile material
        "enrichment": ParameterSpec(
            type="float",
            default=5.0,
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
        # Wall material
        "wall_material": ParameterSpec(
            type="enum",
            options=["ss304", "steel", "aluminum"],
            default="ss304",
            description="Pipe wall material",
        ),

        # Water environment
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
            min=0.0,
            max=100.0,
            unit="cm",
            description="Water thickness (all sides)",
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

        num_pipes = int(p["num_pipes"])

        # Get pipe dimensions
        if p["pipe_size"] == "custom":
            r_inner = p["inner_radius_cm"]
            wall_t = p["wall_thickness_cm"]
            if r_inner is None or wall_t is None:
                raise ValueError("Custom pipe requires inner_radius_cm and wall_thickness_cm")
        else:
            pipe = get_pipe(p["pipe_size"])
            r_inner = pipe.inner_radius_cm
            wall_t = pipe.wall_thickness_cm

        r_outer = r_inner + wall_t
        length = p["length_cm"]
        gap = p["gap_cm"]

        # Pitch (center-to-center distance)
        pitch = 2 * r_outer + gap

        # Calculate pipe center positions along Y axis
        # For 1 pipe: [0]
        # For 2 pipes: [-pitch/2, pitch/2]
        # For 3 pipes: [-pitch, 0, pitch]
        if num_pipes == 1:
            pipe_y_positions = [0.0]
        elif num_pipes == 2:
            pipe_y_positions = [-pitch / 2, pitch / 2]
        else:  # 3 pipes
            pipe_y_positions = [-pitch, 0.0, pitch]

        # Water thickness
        water_t = p["water_thickness_cm"]

        # Array extents
        y_extent = max(abs(y) for y in pipe_y_positions) + r_outer
        y_total = y_extent + water_t

        # X boundaries
        x_inner = length / 2
        x_total = x_inner + water_t

        # Z boundaries (pipe centered at Z=0)
        z_extent = r_outer
        z_total = z_extent + water_t

        # Material densities
        wall_density = get_density(p["wall_material"])
        water_density = p.get("water_density", 1.0)

        # Total bounding box
        total_x = 2 * x_total
        total_y = 2 * y_total
        total_z = 2 * z_total

        return {
            # Fissile material
            "ENRICHMENT": p["enrichment"],
            "UF6_DENSITY": p["uf6_density"],

            # Pipe geometry
            "NUM_PIPES": num_pipes,
            "PIPE_SIZE": p["pipe_size"],
            "R_INNER": r_inner,
            "R_OUTER": r_outer,
            "LENGTH": length,
            "WALL_THICKNESS": wall_t,
            "GAP": gap,
            "PITCH": pitch,

            # Pipe positions
            "PIPE_Y_POSITIONS": pipe_y_positions,

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

            # Water
            "WATER_DENSITY": water_density,
            "WATER_THICKNESS": water_t,

            # Bounding box
            "TOTAL_X": total_x,
            "TOTAL_Y": total_y,
            "TOTAL_Z": total_z,

            # Source position (center pipe)
            "KSRC_X": 0.0,
            "KSRC_Y": 0.0,
            "KSRC_Z": 0.0,
        }


# Export the template class
Template = ParallelPipesTemplate
