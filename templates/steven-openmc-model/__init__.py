"""
Exact OpenMC reproduction of the current ``mcnp-steven-film.inp`` unit cell.

This template is intentionally deck-specific. The user-facing sweep parameter is
the axial fill surface location ``fill_z_cm`` because that is the literal MCNP
surface being varied. The canonical boundary setup is reflective in ``x/y/z``.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class StevenMCNPFilmTemplate(ProblemTemplate):
    """Single unit cell matching the Steven MCNP film deck."""

    PARAMETERS = {
        "fill_z_cm": ParameterSpec(
            type="float",
            default=20.0,
            min=0.01,
            max=100.0,
            unit="cm",
            description="Axial z position of the fill surface inside the 100 cm vessel",
        ),
        "source_z_cm": ParameterSpec(
            type="float",
            default=10.0,
            min=-50.0,
            max=150.0,
            unit="cm",
            description="Preferred MCNP-style ksrc z location",
        ),
        "x_boundary_type": ParameterSpec(
            type="enum",
            options=["reflective", "vacuum"],
            default="reflective",
            description="Boundary condition at x-min/x-max",
        ),
        "y_boundary_type": ParameterSpec(
            type="enum",
            options=["reflective", "vacuum"],
            default="reflective",
            description="Boundary condition at y-min/y-max",
        ),
        "z_boundary_type": ParameterSpec(
            type="enum",
            options=["reflective", "vacuum"],
            default="reflective",
            description="Boundary condition at z-min/z-max",
        ),
    }

    SIMULATION = {
        "PARTICLES": 4800,
        "BATCHES": 200,
        "INACTIVE": 50,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        """Compute exact deck dimensions from the sweepable fill surface."""
        fill_z = float(p.get("fill_z_cm", 20.0))
        z_vessel_bottom = 0.0
        z_vessel_top = 100.0
        h_inner = z_vessel_top - z_vessel_bottom

        return {
            "FILL_Z_CM": fill_z,
            "FILL_HEIGHT_CM": fill_z - z_vessel_bottom,
            "FILL_FRACTION": (fill_z - z_vessel_bottom) / h_inner,
            "SOURCE_Z_CM": float(p.get("source_z_cm", 10.0)),
            "FUEL_RADIUS_CM": 11.70,
            "WATER_OUTER_RADIUS_CM": 12.70,
            "OUTER_RADIUS_CM": 13.0175,
            "HALF_PITCH_XY_CM": 13.5175,
            "Z_VESSEL_BOTTOM_CM": z_vessel_bottom,
            "Z_VESSEL_TOP_CM": z_vessel_top,
            "Z_CAP_BOTTOM_CM": -0.3175,
            "Z_CAP_TOP_CM": 100.3175,
            "Z_BOUNDARY_BOTTOM_CM": -50.0,
            "Z_BOUNDARY_TOP_CM": 150.0,
            "TOTAL_X": 27.035,
            "TOTAL_Y": 27.035,
            "TOTAL_Z": 200.0,
            "X_BOUNDARY_TYPE": p.get("x_boundary_type", "reflective"),
            "Y_BOUNDARY_TYPE": p.get("y_boundary_type", "reflective"),
            "Z_BOUNDARY_TYPE": p.get("z_boundary_type", "reflective"),
        }


Template = StevenMCNPFilmTemplate
