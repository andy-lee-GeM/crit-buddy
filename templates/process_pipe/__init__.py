"""
Process Pipe Template.

A horizontal pipe filled with UF6, with wall and optional reflector.
Supports standard NPS pipe sizes per ASME B36.10M Schedule 10/10S.

Geometry:
    - Horizontal cylinder along X-axis
    - Circular cross-section in YZ plane
    - Wall: SS304 or carbon steel
    - Reflector: Water, concrete, or air surrounding the pipe
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class ProcessPipeTemplate(ProblemTemplate):
    """
    Single horizontal process pipe with fissile material.

    Coordinate system:
        - X: pipe length direction (horizontal)
        - Y: horizontal perpendicular to pipe
        - Z: vertical
        - Origin at center of pipe
    """

    PARAMETERS = {
        # Pipe selection (use standard size OR custom dimensions)
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

        # Pipe length
        "length_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=1000.0,
            unit="cm",
            description="Pipe length",
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

        # Reflector
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

        # Reflector
        refl_t = p["reflector_thickness_cm"]
        if p["reflector_material"] == "none":
            refl_t = 0.0
        r_refl = r_outer + refl_t

        # X boundaries (pipe length direction, centered at 0)
        x_inner = length / 2
        x_outer = x_inner  # Wall is radial only, caps at ends
        x_refl = x_inner + refl_t

        # Material densities
        wall_density = get_density(p["wall_material"])
        refl_density = get_density(p["reflector_material"]) if p["reflector_material"] != "none" else 0.0

        # Total bounding box
        total_x = 2 * x_refl
        total_yz = 2 * r_refl

        return {
            # Fissile material
            "ENRICHMENT": p["enrichment"],
            "UF6_DENSITY": p["uf6_density"],

            # Pipe geometry
            "PIPE_SIZE": p["pipe_size"],
            "R_INNER": r_inner,
            "R_OUTER": r_outer,
            "R_REFL": r_refl,
            "LENGTH": length,
            "WALL_THICKNESS": wall_t,

            # X boundaries
            "X_INNER": x_inner,
            "X_REFL": x_refl,

            # Wall
            "WALL_MATERIAL": p["wall_material"],
            "WALL_DENSITY": wall_density,

            # Reflector
            "REFLECTOR_MATERIAL": p["reflector_material"],
            "REFL_THICKNESS": refl_t,
            "REFL_DENSITY": refl_density,

            # Bounding box
            "TOTAL_X": total_x,
            "TOTAL_YZ": total_yz,

            # Source position (center of pipe)
            "KSRC_X": 0.0,
            "KSRC_Y": 0.0,
            "KSRC_Z": 0.0,
        }


# Export the template class
Template = ProcessPipeTemplate
