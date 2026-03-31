"""
OpenMC model definition for the centrifuge unit cell.

This model exposes design-facing vessel geometry while preserving the current
certified centrifuge unit-cell defaults. The canonical boundary setup remains
reflective in ``x/y/z``.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CentrifugeUnitCellTemplate(ProblemTemplate):
    """Single centrifuge unit cell with geometry-first user inputs."""

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
        "inner_radius_cm": ParameterSpec(
            type="float",
            default=11.70,
            min=0.1,
            max=100.0,
            unit="cm",
            description="Inner fuel radius of the centrifuge vessel",
        ),
        "water_film_thickness_cm": ParameterSpec(
            type="float",
            default=1.0,
            min=0.0,
            max=20.0,
            unit="cm",
            description="Thickness of the water film outside the fuel region",
        ),
        "wall_thickness_cm": ParameterSpec(
            type="float",
            default=0.3175,
            min=0.01,
            max=10.0,
            unit="cm",
            description="Steel wall thickness; also used for the end-cap thickness",
        ),
        "vessel_height_cm": ParameterSpec(
            type="float",
            default=100.0,
            min=1.0,
            max=500.0,
            unit="cm",
            description="Total vessel height (from z=0 to z=vessel_height_cm)",
        ),
        "fill_height_cm": ParameterSpec(
            type="float",
            default=20.0,
            min=0.01,
            max=500.0,
            unit="cm",
            description="Fuel fill height measured from the vessel bottom",
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
        """Compute exact unit-cell dimensions from geometry-first inputs."""
        inner_radius = float(p.get("inner_radius_cm", 11.70))
        water_film_thickness = float(p.get("water_film_thickness_cm", 1.0))
        wall_thickness = float(p.get("wall_thickness_cm", 0.3175))
        fill_height = float(p.get("fill_height_cm", 20.0))
        z_vessel_bottom = 0.0
        vessel_height = float(p.get("vessel_height_cm", 100.0))
        z_vessel_top = vessel_height
        h_inner = z_vessel_top - z_vessel_bottom

        if inner_radius <= 0.0:
            raise ValueError("inner_radius_cm must be positive")
        if water_film_thickness < 0.0:
            raise ValueError("water_film_thickness_cm must be non-negative")
        if wall_thickness <= 0.0:
            raise ValueError("wall_thickness_cm must be positive")
        if fill_height <= 0.0:
            raise ValueError("fill_height_cm must be positive")
        if fill_height > vessel_height:
            raise ValueError("fill_height_cm must not exceed vessel_height_cm")

        water_outer_radius = inner_radius + water_film_thickness
        outer_radius = water_outer_radius + wall_thickness
        half_pitch = outer_radius + 0.5

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
            "FILL_Z_CM": fill_height,
            "FILL_HEIGHT_CM": fill_height,
            "FILL_FRACTION": fill_height / h_inner,
            "SOURCE_Z_CM": float(p.get("source_z_cm", 10.0)),
            "INNER_RADIUS_CM": inner_radius,
            "WATER_FILM_THICKNESS_CM": water_film_thickness,
            "WALL_THICKNESS_CM": wall_thickness,
            "FUEL_RADIUS_CM": inner_radius,
            "WATER_OUTER_RADIUS_CM": water_outer_radius,
            "OUTER_RADIUS_CM": outer_radius,
            "HALF_PITCH_XY_CM": half_pitch,
            "Z_VESSEL_BOTTOM_CM": z_vessel_bottom,
            "Z_VESSEL_TOP_CM": z_vessel_top,
            "Z_CAP_BOTTOM_CM": z_cap_bottom,
            "Z_CAP_TOP_CM": z_cap_top,
            "Z_BOUNDARY_BOTTOM_CM": z_boundary_bottom,
            "Z_BOUNDARY_TOP_CM": z_boundary_top,
            "TOTAL_X": 2.0 * half_pitch,
            "TOTAL_Y": 2.0 * half_pitch,
            "TOTAL_Z": total_z,
            "X_BOUNDARY_TYPE": p.get("x_boundary_type", "reflective"),
            "Y_BOUNDARY_TYPE": p.get("y_boundary_type", "reflective"),
            "Z_BOUNDARY_TYPE": p.get("z_boundary_type", "reflective"),
        }


Template = CentrifugeUnitCellTemplate
