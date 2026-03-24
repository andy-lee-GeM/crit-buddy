"""
Reflected linear pipe model for AD-7 parity work.

This model follows the same "literal unit-cell with explicit boundary planes"
pattern used by ``centrifuge-unit-cell``. Geometry and materials follow the
original MCNP piping reference: a central UF6 gas core, a 1 cm annular UO2F2
layer, an aluminum wall, and water moderator outside the pipe.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec
from critbuddy.core.geometry.pipes import PIPE_REGISTRY, get_pipe


class PipeLinearModelTemplate(ProblemTemplate):
    """Single reflected linear pipe model matching the original MCNP reference style."""

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
            description="Outer pipe radius for custom sizing",
        ),
        "pipe_wall_thickness_cm": ParameterSpec(
            type="float",
            default=0.3048,
            min=0.05,
            max=5.0,
            unit="cm",
            description="Pipe wall thickness for custom sizing",
        ),
        "gas_core_radius_cm": ParameterSpec(
            type="float",
            default=4.4102,
            min=0.05,
            max=50.0,
            unit="cm",
            description="Radius of the central UF6 gas core",
        ),
        "fuel_outer_radius_cm": ParameterSpec(
            type="float",
            default=5.4102,
            min=0.05,
            max=50.0,
            unit="cm",
            description="Outer radius of the annular UO2F2 layer",
        ),
        "uf6_density_g_cm3": ParameterSpec(
            type="float",
            default=0.0127,
            min=1.0e-6,
            max=20.0,
            unit="g/cm3",
            description="UF6 gas density",
        ),
        "uo2f2_density_g_cm3": ParameterSpec(
            type="float",
            default=6.37,
            min=0.01,
            max=20.0,
            unit="g/cm3",
            description="Dry UO2F2 density",
        ),
        "separation_cm": ParameterSpec(
            type="float",
            default=6.4,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Edge-to-edge separation to reflected neighboring pipes",
        ),
        "axial_height_cm": ParameterSpec(
            type="float",
            default=17.43,
            min=1.0,
            max=500.0,
            unit="cm",
            description="Axial unit-cell height",
        ),
        "wall_material": ParameterSpec(
            type="enum",
            options=["aluminum", "ss304"],
            default="aluminum",
            description="Pipe wall material",
        ),
        "moderator_density_g_cm3": ParameterSpec(
            type="float",
            default=1.0,
            min=0.01,
            max=2.0,
            unit="g/cm3",
            description="Water moderator density",
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
        """Compute exact unit-cell dimensions from the requested separation."""
        pipe_size = p.get("pipe_size", "4")
        if pipe_size == "custom":
            outer_radius = float(p.get("pipe_outer_radius_cm", 5.715))
            wall_thickness = float(p.get("pipe_wall_thickness_cm", 0.3048))
            inner_radius = outer_radius - wall_thickness
        else:
            spec = get_pipe(str(pipe_size))
            outer_radius = spec.outer_radius_cm
            wall_thickness = spec.wall_thickness_cm
            inner_radius = spec.inner_radius_cm
        gas_core_radius = float(p.get("gas_core_radius_cm", 4.4102))
        fuel_outer_radius = float(p.get("fuel_outer_radius_cm", 5.4102))

        if gas_core_radius <= 0.0:
            raise ValueError("gas_core_radius_cm must be positive")
        if gas_core_radius >= fuel_outer_radius:
            raise ValueError("gas_core_radius_cm must be less than fuel_outer_radius_cm")
        if fuel_outer_radius > inner_radius + 1.0e-3:
            raise ValueError("fuel_outer_radius_cm must not exceed the pipe inner radius")

        separation = float(p.get("separation_cm", 6.4))
        half_pitch = outer_radius + 0.5 * separation
        axial_height = float(p.get("axial_height_cm", 17.43))
        half_height = axial_height / 2.0

        return {
            "ENRICHMENT_PCT": float(p.get("enrichment_pct", 20.2)),
            "PIPE_SIZE": pipe_size,
            "PIPE_OUTER_RADIUS_CM": outer_radius,
            "PIPE_INNER_RADIUS_CM": inner_radius,
            "PIPE_WALL_THICKNESS_CM": wall_thickness,
            "GAS_CORE_RADIUS_CM": gas_core_radius,
            "FUEL_OUTER_RADIUS_CM": fuel_outer_radius,
            "UF6_DENSITY_G_CM3": float(p.get("uf6_density_g_cm3", 0.0127)),
            "UO2F2_DENSITY_G_CM3": float(p.get("uo2f2_density_g_cm3", 6.37)),
            "SEPARATION_CM": separation,
            "HALF_PITCH_CM": half_pitch,
            "AXIAL_HEIGHT_CM": axial_height,
            "HALF_HEIGHT_CM": half_height,
            "TOTAL_X": 2.0 * half_pitch,
            "TOTAL_Y": 2.0 * half_pitch,
            "TOTAL_Z": axial_height,
            "WALL_MATERIAL": p.get("wall_material", "aluminum"),
            "MODERATOR_DENSITY_G_CM3": float(p.get("moderator_density_g_cm3", 1.0)),
            "SOURCE_Z_CM": 0.0,
            "X_BOUNDARY_TYPE": p.get("x_boundary_type", "reflective"),
            "Y_BOUNDARY_TYPE": p.get("y_boundary_type", "reflective"),
            "Z_BOUNDARY_TYPE": p.get("z_boundary_type", "reflective"),
        }


Template = PipeLinearModelTemplate
