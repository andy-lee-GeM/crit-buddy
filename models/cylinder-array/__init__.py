"""
OpenMC model definition for a finite centrifuge-style cylinder array.

This model reuses the maintained centrifuge vessel geometry and places it in a
finite x/y/z arrangement. User-facing axes are:

- x: horizontal
- y: vertical
- z: depth

Internally, the OpenMC geometry keeps the vessel axis aligned with the OpenMC
z-axis and remaps user y/z onto OpenMC z/y respectively.
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CylinderArrayTemplate(ProblemTemplate):
    """Finite array of capped cylinders with uniform wall-to-wall spacing."""

    PARAMETERS = {
        "fissile_material": ParameterSpec(
            type="enum",
            options=["uf6", "uo2f2"],
            default="uo2f2",
            description="Fissile material type used in the filled region",
        ),
        "enrichment_pct": ParameterSpec(
            type="float",
            default=20.2,
            min=0.1,
            max=100.0,
            unit="%",
            description="U-235 weight percent enrichment",
        ),
        "fissile_density_g_cm3": ParameterSpec(
            type="float",
            default=None,
            min=0.00001,
            max=20.0,
            unit="g/cm3",
            description="Optional fissile material density override; for UO2F2 the default is derived from h_to_u",
        ),
        "h_to_u": ParameterSpec(
            type="float",
            default=5.0,
            min=0.0,
            max=100.0,
            description="Hydrogen to uranium atomic ratio for UO2F2 cases",
        ),
        "inner_radius_cm": ParameterSpec(
            type="float",
            default=11.70,
            min=0.1,
            max=100.0,
            unit="cm",
            description="Inner fuel radius of the cylinder",
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
            description="Inner vessel height excluding end caps",
        ),
        "fill_height_cm": ParameterSpec(
            type="float",
            default=20.0,
            min=0.01,
            max=500.0,
            unit="cm",
            description="Fuel fill height measured from the vessel bottom",
        ),
        "fill_fraction_percent": ParameterSpec(
            type="float",
            default=None,
            min=0.001,
            max=100.0,
            unit="%",
            description="Fuel fill expressed as a percent of vessel height; overrides fill_height_cm when provided",
        ),
        "num_cylinders_x": ParameterSpec(
            type="int",
            default=1,
            min=1,
            max=200,
            description="Number of cylinders in the horizontal x direction",
        ),
        "num_cylinders_y": ParameterSpec(
            type="int",
            default=1,
            min=1,
            max=200,
            description="Number of cylinders in the vertical y direction",
        ),
        "num_cylinders_z": ParameterSpec(
            type="int",
            default=1,
            min=1,
            max=200,
            description="Number of cylinders in the depth z direction",
        ),
        "wall_to_wall_gap_cm": ParameterSpec(
            type="float",
            default=1.0,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Uniform wall-to-wall and cap-to-cap gap between adjacent cylinders",
        ),
        "edge_moderator_thickness_cm": ParameterSpec(
            type="float",
            default=50.0,
            min=0.0,
            max=500.0,
            unit="cm",
            description="Thickness of the outer water moderator shell before the boundary",
        ),
        "x_boundary_type": ParameterSpec(
            type="enum",
            options=["reflective", "vacuum"],
            default="vacuum",
            description="Boundary condition at x-min/x-max",
        ),
        "y_boundary_type": ParameterSpec(
            type="enum",
            options=["reflective", "vacuum"],
            default="vacuum",
            description="Boundary condition at y-min/y-max (vertical)",
        ),
        "z_boundary_type": ParameterSpec(
            type="enum",
            options=["reflective", "vacuum"],
            default="vacuum",
            description="Boundary condition at z-min/z-max (depth)",
        ),
    }

    SIMULATION = {
        "PARTICLES": 4800,
        "BATCHES": 200,
        "INACTIVE": 50,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        """Compute finite-array dimensions from geometry-first inputs."""
        inner_radius = float(p.get("inner_radius_cm", 11.70))
        water_film_thickness = float(p.get("water_film_thickness_cm", 1.0))
        wall_thickness = float(p.get("wall_thickness_cm", 0.3175))
        vessel_height = float(p.get("vessel_height_cm", 100.0))
        gap = float(p.get("wall_to_wall_gap_cm", 1.0))
        edge_moderator_thickness = float(p.get("edge_moderator_thickness_cm", 50.0))
        fill_fraction_percent = p.get("fill_fraction_percent")
        fissile_material = str(p.get("fissile_material", "uo2f2")).lower()
        fissile_density = p.get("fissile_density_g_cm3")

        num_x = int(p.get("num_cylinders_x", 1))
        num_y = int(p.get("num_cylinders_y", 1))
        num_z = int(p.get("num_cylinders_z", 1))

        if fill_fraction_percent is not None:
            fill_fraction = float(fill_fraction_percent) / 100.0
            fill_height = vessel_height * fill_fraction
        else:
            fill_height = float(p.get("fill_height_cm", 20.0))
            fill_fraction = fill_height / vessel_height

        if inner_radius <= 0.0:
            raise ValueError("inner_radius_cm must be positive")
        if water_film_thickness < 0.0:
            raise ValueError("water_film_thickness_cm must be non-negative")
        if wall_thickness <= 0.0:
            raise ValueError("wall_thickness_cm must be positive")
        if vessel_height <= 0.0:
            raise ValueError("vessel_height_cm must be positive")
        if fill_height <= 0.0:
            raise ValueError("Resolved fill height must be positive")
        if fill_height > vessel_height:
            raise ValueError("Resolved fill height must not exceed vessel_height_cm")
        if gap < 0.0:
            raise ValueError("wall_to_wall_gap_cm must be non-negative")
        if edge_moderator_thickness < 0.0:
            raise ValueError("edge_moderator_thickness_cm must be non-negative")
        if min(num_x, num_y, num_z) < 1:
            raise ValueError("Cylinder counts must all be at least 1")
        if fissile_material not in {"uf6", "uo2f2"}:
            raise ValueError("fissile_material must be either 'uf6' or 'uo2f2'")
        if fissile_material == "uo2f2" and "h_to_u" not in p:
            # Defaults still apply, but this keeps the dependency explicit in the
            # derived output and error paths for future callers.
            pass

        water_outer_radius = inner_radius + water_film_thickness
        outer_radius = water_outer_radius + wall_thickness
        outer_diameter = 2.0 * outer_radius
        outer_height = vessel_height + 2.0 * wall_thickness

        pitch_x = outer_diameter + gap
        pitch_y = outer_height + gap
        pitch_z = outer_diameter + gap

        array_x = outer_diameter + (num_x - 1) * pitch_x
        array_y = outer_height + (num_y - 1) * pitch_y
        array_z = outer_diameter + (num_z - 1) * pitch_z

        total_x = array_x + 2.0 * edge_moderator_thickness
        total_y = array_y + 2.0 * edge_moderator_thickness
        total_z = array_z + 2.0 * edge_moderator_thickness

        lattice_span_x = num_x * pitch_x
        lattice_span_y = num_y * pitch_y
        lattice_span_z = num_z * pitch_z

        local_z_vessel_bottom = -0.5 * vessel_height
        local_z_vessel_top = 0.5 * vessel_height
        local_z_cap_bottom = -0.5 * outer_height
        local_z_cap_top = 0.5 * outer_height
        local_fill_z = local_z_vessel_bottom + fill_height

        return {
            "FISSILE_MATERIAL": fissile_material,
            "ENRICHMENT_PCT": float(p.get("enrichment_pct", 20.2)),
            "FISSILE_DENSITY_G_CM3": None if fissile_density is None else float(fissile_density),
            "H_TO_U": float(p.get("h_to_u", 5.0)),
            "WALL_MATERIAL": "stainless_steel_316",
            "WATER_MATERIAL": "water",
            "WATER_DENSITY_G_CM3": 1.0,
            "AIR_MATERIAL": "centrifuge_air",
            "FILL_HEIGHT_CM": fill_height,
            "FILL_FRACTION": fill_fraction,
            "FILL_FRACTION_PERCENT": 100.0 * fill_fraction,
            "INNER_RADIUS_CM": inner_radius,
            "WATER_FILM_THICKNESS_CM": water_film_thickness,
            "WALL_THICKNESS_CM": wall_thickness,
            "FUEL_RADIUS_CM": inner_radius,
            "WATER_OUTER_RADIUS_CM": water_outer_radius,
            "OUTER_RADIUS_CM": outer_radius,
            "OUTER_DIAMETER_CM": outer_diameter,
            "VESSEL_HEIGHT_CM": vessel_height,
            "OUTER_HEIGHT_CM": outer_height,
            "NUM_CYLINDERS_X": num_x,
            "NUM_CYLINDERS_Y": num_y,
            "NUM_CYLINDERS_Z": num_z,
            "TOTAL_CYLINDERS": num_x * num_y * num_z,
            "WALL_TO_WALL_GAP_CM": gap,
            "EDGE_MODERATOR_THICKNESS_CM": edge_moderator_thickness,
            "PITCH_X_CM": pitch_x,
            "PITCH_Y_CM": pitch_y,
            "PITCH_Z_CM": pitch_z,
            "ARRAY_X_CM": array_x,
            "ARRAY_Y_CM": array_y,
            "ARRAY_Z_CM": array_z,
            "TOTAL_X_CM": total_x,
            "TOTAL_Y_CM": total_y,
            "TOTAL_Z_CM": total_z,
            "LATTICE_SPAN_X_CM": lattice_span_x,
            "LATTICE_SPAN_Y_CM": lattice_span_y,
            "LATTICE_SPAN_Z_CM": lattice_span_z,
            "LOCAL_Z_VESSEL_BOTTOM_CM": local_z_vessel_bottom,
            "LOCAL_Z_VESSEL_TOP_CM": local_z_vessel_top,
            "LOCAL_Z_CAP_BOTTOM_CM": local_z_cap_bottom,
            "LOCAL_Z_CAP_TOP_CM": local_z_cap_top,
            "LOCAL_FILL_Z_CM": local_fill_z,
            "X_BOUNDARY_TYPE": p.get("x_boundary_type", "vacuum"),
            "Y_BOUNDARY_TYPE": p.get("y_boundary_type", "vacuum"),
            "Z_BOUNDARY_TYPE": p.get("z_boundary_type", "vacuum"),
        }


Template = CylinderArrayTemplate
