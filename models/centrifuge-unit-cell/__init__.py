"""
OpenMC model definition for the centrifuge unit cell.

This model is intentionally deck-specific. The user-facing sweep parameter is
the axial fill surface location ``fill_z_cm`` because that is the literal MCNP
surface being varied. The canonical boundary setup is reflective in ``x/y/z``.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CentrifugeThinFilmTemplate(ProblemTemplate):
    """Single unit cell matching the canonical centrifuge unit cell deck."""

    PARAMETERS = {
        "enrichment_pct": ParameterSpec(
            type="float",
            default=20.2,
            min=0.1,
            max=100.0,
            unit="%",
            description="U-235 weight percent enrichment",
        ),
        "h_to_u": ParameterSpec(
            type="float",
            default=5.0,
            min=0.0,
            max=100.0,
            description="Hydrogen to uranium atomic ratio",
        ),
        "vessel_height_cm": ParameterSpec(
            type="float",
            default=100.0,
            min=1.0,
            max=500.0,
            unit="cm",
            description="Total vessel height (from z=0 to z=vessel_height_cm)",
        ),
        "fill_z_cm": ParameterSpec(
            type="float",
            default=20.0,
            min=0.01,
            max=100.0,
            unit="cm",
            description="Axial z position of the fill surface inside the vessel",
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
        vessel_height = float(p.get("vessel_height_cm", 100.0))
        z_vessel_top = vessel_height
        h_inner = z_vessel_top - z_vessel_bottom

        # End cap thickness
        wall_thickness = 0.3175
        z_cap_bottom = z_vessel_bottom - wall_thickness
        z_cap_top = z_vessel_top + wall_thickness

        # Boundary box extends beyond vessel
        z_boundary_bottom = z_vessel_bottom - 50.0
        z_boundary_top = z_vessel_top + 50.0
        total_z = z_boundary_top - z_boundary_bottom

        return {
            "ENRICHMENT_PCT": float(p.get("enrichment_pct", 20.2)),
            "H_TO_U": float(p.get("h_to_u", 5.0)),
            "FISSILE_MATERIAL": "uo2f2",
            "WALL_MATERIAL": "stainless_steel_316",
            "WATER_MATERIAL": "water",
            "WATER_DENSITY_G_CM3": 1.0,
            "AIR_MATERIAL": "centrifuge_air",
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
            "Z_CAP_BOTTOM_CM": z_cap_bottom,
            "Z_CAP_TOP_CM": z_cap_top,
            "Z_BOUNDARY_BOTTOM_CM": z_boundary_bottom,
            "Z_BOUNDARY_TOP_CM": z_boundary_top,
            "TOTAL_X": 27.035,
            "TOTAL_Y": 27.035,
            "TOTAL_Z": total_z,
            "X_BOUNDARY_TYPE": p.get("x_boundary_type", "reflective"),
            "Y_BOUNDARY_TYPE": p.get("y_boundary_type", "reflective"),
            "Z_BOUNDARY_TYPE": p.get("z_boundary_type", "reflective"),
        }


Template = CentrifugeThinFilmTemplate
