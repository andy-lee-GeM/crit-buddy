"""
OpenMC model definition for a single pipe unit cell with UO2F2 fill.

This model represents a single cylindrical pipe with UO2F2 solution,
optionally with partial fill and headspace gas. The canonical configuration
uses reflective boundaries to simulate an infinite lattice.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec
from critbuddy.core.geometry.pipes import PIPE_REGISTRY, get_pipe


class PipeUnitCellTemplate(ProblemTemplate):
    """Single pipe unit cell with parametric fill fraction."""

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
        "pipe_size": ParameterSpec(
            type="enum",
            options=PIPE_SIZE_OPTIONS,
            default="custom",
            description="Standard NPS pipe size or 'custom' for explicit dimensions",
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
            description="Boundary condition for all faces (reflective=infinite lattice)",
        ),
    }

    SIMULATION = {
        "PARTICLES": 4800,
        "BATCHES": 200,
        "INACTIVE": 50,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        """Compute geometry parameters from input specs."""
        pipe_size = p.get("pipe_size", "custom")
        if pipe_size == "custom":
            outer_r = float(p.get("pipe_outer_radius_cm", 5.715))
            wall_t = float(p.get("pipe_wall_thickness_cm", 0.3048))
        else:
            pipe = get_pipe(str(pipe_size))
            outer_r = pipe.outer_radius_cm
            wall_t = pipe.wall_thickness_cm

        solution_gap = float(p.get("solution_gap_cm", 1.0))
        height = float(p.get("pipe_height_cm", 17.43))
        fill_frac = float(p.get("fill_fraction", 1.0))

        inner_r = outer_r - wall_t
        solution_r_value = p.get("solution_radius_cm")
        if solution_r_value is None:
            solution_r = inner_r - solution_gap
        else:
            solution_r = float(solution_r_value)

        if solution_r <= 0.0:
            raise ValueError("Derived solution radius must be positive")
        if solution_r >= inner_r:
            raise ValueError("Solution radius must remain inside the pipe inner radius")

        fill_height = height * fill_frac
        half_height = height / 2.0

        # Pitch for unit cell (boundary extends slightly beyond pipe)
        pitch = outer_r * 2.2

        return {
            "ENRICHMENT_PCT": float(p.get("enrichment_pct", 20.2)),
            "PIPE_SIZE": pipe_size,
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
            "HALF_PITCH_CM": pitch / 2.0,
            "BOUNDARY_TYPE": p.get("boundary_type", "reflective"),
        }


Template = PipeUnitCellTemplate
