"""
Homogeneous UO2F2-H2O sphere with external water reflection.

This model is intended for benchmark-style moderation studies where the paper
or reference basis is expressed in H/X (hydrogen-to-fissile) but the shared
material builders consume H/U (hydrogen-to-uranium). The template accepts
either input form, derives the exact companion ratio, and builds a simple
homogeneous fissile sphere with a surrounding water reflector.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec
from critbuddy.core.materials.uo2f2_physics import h_u_to_h_x, h_x_to_h_u, uo2f2_density


class UO2F2SphereBenchmarkTemplate(ProblemTemplate):
    """Homogeneous UO2F2-H2O sphere benchmark template."""

    PARAMETERS = {
        "enrichment_pct": ParameterSpec(
            type="float",
            default=20.0,
            min=0.1,
            max=100.0,
            unit="%",
            description="U-235 weight percent enrichment",
        ),
        "h_over_x": ParameterSpec(
            type="float",
            min=0.0,
            max=5000.0,
            description="Hydrogen-to-fissile atomic ratio used by the benchmark paper",
        ),
        "h_to_u": ParameterSpec(
            type="float",
            min=0.0,
            max=5000.0,
            description="Hydrogen-to-uranium atomic ratio used by the shared UO2F2 builder",
        ),
        "sphere_radius_cm": ParameterSpec(
            type="float",
            default=15.0,
            min=0.1,
            max=500.0,
            unit="cm",
            description="Fuel sphere radius",
        ),
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=100.0,
            min=0.0,
            max=500.0,
            unit="cm",
            description="External water-reflector thickness",
        ),
        "reflector_density_g_cm3": ParameterSpec(
            type="float",
            default=1.0,
            min=0.01,
            max=2.0,
            unit="g/cm3",
            description="Water-reflector density",
        ),
        "outer_boundary_type": ParameterSpec(
            type="enum",
            options=["vacuum", "reflective"],
            default="vacuum",
            description="Boundary condition at the outer reflector sphere",
        ),
    }

    SIMULATION = {
        "PARTICLES": 6000,
        "BATCHES": 180,
        "INACTIVE": 40,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        enrichment_pct = float(p.get("enrichment_pct", 20.0))

        raw_h_over_x = p.get("h_over_x")
        raw_h_to_u = p.get("h_to_u")
        if raw_h_over_x is not None and raw_h_to_u is not None:
            raise ValueError("Specify either h_over_x or h_to_u, not both")
        if raw_h_over_x is None and raw_h_to_u is None:
            raise ValueError("Specify one of h_over_x or h_to_u")

        if raw_h_over_x is not None:
            h_over_x = float(raw_h_over_x)
            h_to_u = h_x_to_h_u(h_over_x, enrichment_pct)
            moderation_input_mode = "paper_h_over_x"
        else:
            h_to_u = float(raw_h_to_u)
            h_over_x = h_u_to_h_x(h_to_u, enrichment_pct)
            moderation_input_mode = "direct_h_to_u"

        sphere_radius_cm = float(p.get("sphere_radius_cm", 15.0))
        reflector_thickness_cm = float(p.get("reflector_thickness_cm", 100.0))
        outer_radius_cm = sphere_radius_cm + reflector_thickness_cm
        if outer_radius_cm <= sphere_radius_cm:
            raise ValueError("reflector_thickness_cm must not make the outer radius shrink")

        fuel_density = uo2f2_density(h_to_u=h_to_u, enrichment_pct=enrichment_pct)
        fuel_volume_cm3 = (4.0 / 3.0) * 3.141592653589793 * sphere_radius_cm**3
        outer_volume_cm3 = (4.0 / 3.0) * 3.141592653589793 * outer_radius_cm**3

        return {
            "ENRICHMENT_PCT": enrichment_pct,
            "H_OVER_X": h_over_x,
            "H_TO_U": h_to_u,
            "MODERATION_INPUT_MODE": moderation_input_mode,
            "SPHERE_RADIUS_CM": sphere_radius_cm,
            "REFLECTOR_THICKNESS_CM": reflector_thickness_cm,
            "OUTER_RADIUS_CM": outer_radius_cm,
            "REFLECTOR_DENSITY_G_CM3": float(p.get("reflector_density_g_cm3", 1.0)),
            "OUTER_BOUNDARY_TYPE": p.get("outer_boundary_type", "vacuum"),
            "UO2F2_DENSITY_G_CM3": fuel_density,
            "FUEL_VOLUME_CM3": fuel_volume_cm3,
            "FUEL_VOLUME_L": fuel_volume_cm3 / 1000.0,
            "OUTER_VOLUME_CM3": outer_volume_cm3,
            "OUTER_VOLUME_L": outer_volume_cm3 / 1000.0,
            "PLOT_WIDTH_CM": 2.1 * outer_radius_cm,
        }


Template = UO2F2SphereBenchmarkTemplate
