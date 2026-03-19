"""
OpenMC model definition for pipe array configurations.

This model represents multiple pipes arranged in various configurations:
- Linear array (pipes in a line along x-axis)
- Grid array (future: crossing pipes in x and y)
- Triangular pitch (future: close-packed hexagonal)

The default 2-pipe configuration matches the MCNP reference case.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec
from critbuddy.core.geometry.pipes import PIPE_REGISTRY, get_pipe


class PipeArrayTemplate(ProblemTemplate):
    """Multiple pipes in array configuration with parametric spacing."""

    PIPE_SIZE_OPTIONS = [*PIPE_REGISTRY.keys(), "custom"]

    PARAMETERS = {
        "enrichment_pct": ParameterSpec(
            type="float",
            default=20.2,
            min=0.1,
            max=100.0,
            unit="%",
            description="U-235 weight percent enrichment",
        ),
        "n_pipes": ParameterSpec(
            type="int",
            default=2,
            min=1,
            max=20,
            description="Number of pipes in linear array",
        ),
        "pipe_size": ParameterSpec(
            type="enum",
            options=PIPE_SIZE_OPTIONS,
            default="custom",
            description="Standard NPS pipe size or 'custom' for explicit dimensions",
        ),
        "pipe_pitch_cm": ParameterSpec(
            type="float",
            default=11.43,
            min=1.0,
            max=100.0,
            unit="cm",
            description="Center-to-center spacing between pipes",
        ),
        "edge_spacing_cm": ParameterSpec(
            type="float",
            default=None,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Optional edge-to-edge spacing; overrides pipe_pitch_cm when provided",
        ),
        "pipe_outer_radius_cm": ParameterSpec(
            type="float",
            default=5.715,
            min=0.5,
            max=50.0,
            unit="cm",
            description="Outer radius of pipe wall",
        ),
        "pipe_wall_thickness_cm": ParameterSpec(
            type="float",
            default=0.3048,
            min=0.05,
            max=2.0,
            unit="cm",
            description="Pipe wall thickness",
        ),
        "solution_radius_cm": ParameterSpec(
            type="float",
            default=None,
            min=0.5,
            max=50.0,
            unit="cm",
            description="Radius of UO2F2 solution (inside gas gap); leave unset to derive from pipe size and gap",
        ),
        "solution_gap_cm": ParameterSpec(
            type="float",
            default=1.0,
            min=0.0,
            max=10.0,
            unit="cm",
            description="Radial UF6 gas gap between solution and pipe inner wall",
        ),
        "pipe_height_cm": ParameterSpec(
            type="float",
            default=17.43,
            min=5.0,
            max=200.0,
            unit="cm",
            description="Total height of pipe segment",
        ),
        "fill_fraction": ParameterSpec(
            type="float",
            default=1.0,
            min=0.01,
            max=1.0,
            description="Fraction of pipe filled with UO2F2 (0.0-1.0)",
        ),
        "boundary_type": ParameterSpec(
            type="enum",
            options=["reflective", "vacuum"],
            default="reflective",
            description="Boundary condition (reflective=infinite array)",
        ),
        "include_water": ParameterSpec(
            type="bool",
            default=True,
            description="Include water moderator/reflector around pipes",
        ),
    }

    SIMULATION = {
        "PARTICLES": 4800,
        "BATCHES": 200,
        "INACTIVE": 50,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        """Compute geometry parameters for pipe array."""
        n_pipes = int(p.get("n_pipes", 2))
        pipe_size = p.get("pipe_size", "custom")
        if pipe_size == "custom":
            outer_r = float(p.get("pipe_outer_radius_cm", 5.715))
            wall_t = float(p.get("pipe_wall_thickness_cm", 0.3048))
        else:
            pipe = get_pipe(str(pipe_size))
            outer_r = pipe.outer_radius_cm
            wall_t = pipe.wall_thickness_cm

        edge_spacing_input = p.get("edge_spacing_cm")
        if edge_spacing_input is None:
            pitch = float(p.get("pipe_pitch_cm", 11.43))
            edge_spacing = pitch - 2 * outer_r
        else:
            edge_spacing = float(edge_spacing_input)
            pitch = edge_spacing + 2 * outer_r

        solution_gap = float(p.get("solution_gap_cm", 1.0))
        height = float(p.get("pipe_height_cm", 17.43))
        fill_frac = float(p.get("fill_fraction", 1.0))

        inner_r = outer_r - wall_t
        solution_r_value = p.get("solution_radius_cm")
        if solution_r_value is None:
            solution_r = inner_r - solution_gap
        else:
            solution_r = float(solution_r_value)

        if pitch < 2 * outer_r:
            raise ValueError("Pipe pitch must be at least the pipe outer diameter")
        if solution_r <= 0.0:
            raise ValueError("Derived solution radius must be positive")
        if solution_r >= inner_r:
            raise ValueError("Solution radius must remain inside the pipe inner radius")

        fill_height = height * fill_frac
        half_height = height / 2.0

        # Array extent (with margin for boundaries)
        if n_pipes == 1:
            array_width_x = outer_r * 4.0
        else:
            array_width_x = (n_pipes - 1) * pitch + 2 * outer_r * 2.0

        # Boundary positions (MCNP-style: match reference case for 2-pipe)
        if n_pipes == 2 and pitch == 11.43:
            # Match MCNP reference exactly
            x_min = -8.715
            x_max = 8.815  # Note asymmetry in MCNP reference
            y_min = -8.715
            y_max = 20.145
        else:
            # General case: symmetric boundaries with margin
            x_min = -(n_pipes - 1) * pitch / 2.0 - outer_r * 1.5
            x_max = (n_pipes - 1) * pitch / 2.0 + outer_r * 1.5
            y_min = -outer_r * 2.5
            y_max = outer_r * 2.5

        # Pipe centers along x-axis (centered at origin for n_pipes=2)
        if n_pipes == 1:
            pipe_centers_x = [0.0]
        elif n_pipes == 2:
            # Match MCNP: first pipe at origin, second at +pitch
            pipe_centers_x = [0.0, pitch]
        else:
            # General: centered array
            start_x = -(n_pipes - 1) * pitch / 2.0
            pipe_centers_x = [start_x + i * pitch for i in range(n_pipes)]

        return {
            "ENRICHMENT_PCT": float(p.get("enrichment_pct", 20.2)),
            "N_PIPES": n_pipes,
            "PIPE_SIZE": pipe_size,
            "PIPE_PITCH_CM": pitch,
            "EDGE_SPACING_CM": edge_spacing,
            "PIPE_OUTER_RADIUS_CM": outer_r,
            "PIPE_INNER_RADIUS_CM": inner_r,
            "PIPE_WALL_THICKNESS_CM": wall_t,
            "SOLUTION_RADIUS_CM": solution_r,
            "SOLUTION_GAP_CM": inner_r - solution_r,
            "PIPE_HEIGHT_CM": height,
            "PIPE_HALF_HEIGHT_CM": half_height,
            "FILL_FRACTION": fill_frac,
            "FILL_HEIGHT_CM": fill_height,
            "FILL_Z_TOP_CM": fill_height - half_height,
            "Z_MIN_CM": -half_height,
            "Z_MAX_CM": half_height,
            "X_MIN_CM": x_min,
            "X_MAX_CM": x_max,
            "Y_MIN_CM": y_min,
            "Y_MAX_CM": y_max,
            "PIPE_CENTERS_X": pipe_centers_x,
            "BOUNDARY_TYPE": p.get("boundary_type", "reflective"),
            "INCLUDE_WATER": bool(p.get("include_water", True)),
        }


Template = PipeArrayTemplate
