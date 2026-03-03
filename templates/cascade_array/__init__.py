"""
Cascade Array Problem Template.

A hierarchical array of cylinders organized as:
    - Cylinders within a pack (i x j x k lattice)

Geometry Hierarchy:
    Level 1: Cylinder    - Single steel-clad vessel with fissile material
    Level 2: Pack        - i x j x k lattice of cylinders
    Level 3: Pack + boundary shell (ROOT)

Applications: Cascade hall layouts, process equipment arrays
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CascadeArrayTemplate(ProblemTemplate):
    """
    Cascade array template with nested universe hierarchy.

    Coordinate system:
        - X: cylinder count direction within pack (i)
        - Y: cylinder count direction within pack (j)
        - Z: vertical stacking direction (k)
        - Origin at pack corner (not centered)
    """

    PARAMETERS = {
        # =====================================================================
        # FISSILE MATERIAL
        # =====================================================================
        "enrichment": ParameterSpec(
            type="float",
            default=5.0,
            min=0.7,
            max=100.0,
            unit="wt%",
            description="U-235 enrichment (weight percent)",
        ),
        "fissile_material": ParameterSpec(
            type="enum",
            options=["uf6", "uo2f2"],
            default="uf6",
            description="Fissile material type (uf6 or uo2f2)",
        ),
        "fissile_density": ParameterSpec(
            type="float",
            default=None,
            min=1.0,
            max=7.0,
            unit="g/cc",
            description="Optional fissile material density override (UF6 default: 5.09)",
        ),
        "h_to_u": ParameterSpec(
            type="float",
            required=False,
            default=0.0,
            min=0.0,
            max=500.0,
            unit="",
            description="H/U atomic ratio for wet UO2F2 (0 = dry, higher = more water)",
        ),
        # =====================================================================
        # CYLINDER GEOMETRY
        # =====================================================================
        "R_inner_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=50.0,
            unit="cm",
            description="Inner radius of cylinder cavity",
        ),
        "H_inner_cm": ParameterSpec(
            type="float",
            required=True,
            min=1.0,
            max=500.0,
            unit="cm",
            description="Inner height of cylinder cavity",
        ),
        "t_wall_cm": ParameterSpec(
            type="float",
            default=0.3175,
            min=0.0,
            max=5.0,
            unit="cm",
            description="Steel wall thickness (default 1/8 inch)",
        ),
        "wall_material": ParameterSpec(
            type="enum",
            options=["steel", "aluminum"],
            default="steel",
            description="Container wall material",
        ),
        # =====================================================================
        # ARRAY CONFIGURATION
        # =====================================================================
        "i": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=20,
            description="Cylinders per pack in X direction",
        ),
        "j": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=20,
            description="Cylinders per pack in Y direction",
        ),
        "k": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=10,
            description="Cylinders per pack in Z direction (layers)",
        ),
        "gap_xy_cm": ParameterSpec(
            type="float",
            default=0.0,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Horizontal wall-to-wall gap in X/Y directions",
        ),
        "gap_z_cm": ParameterSpec(
            type="float",
            default=0.0,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Vertical cap-to-cap gap in Z direction",
        ),
        # =====================================================================
        # ENVIRONMENT
        # =====================================================================
        "environment_material": ParameterSpec(
            type="enum",
            options=["humid_air", "air"],
            default="humid_air",
            description="Material between units (inside cascade) - humid air or dry air only",
        ),
        "environment_density": ParameterSpec(
            type="float",
            default=None,
            min=0.00001,
            max=2.0,
            unit="g/cc",
            description="Optional environment density override",
        ),
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=5.0,
            max=100.0,
            unit="cm",
            description="Environment shell thickness for finite (vacuum boundary) cases",
        ),
        "boundary_type": ParameterSpec(
            type="enum",
            options=["vacuum", "reflective"],
            default="vacuum",
            description="Boundary condition: vacuum (finite) or reflective (infinite lattice)",
        ),
    }

    SIMULATION = {
        "PARTICLES": 10000,
        "BATCHES": 150,
        "INACTIVE": 50,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        """
        Compute derived geometry parameters from user inputs.

        Naming convention:
            - User inputs: lowercase with _cm suffix (e.g., R_inner_cm)
            - Derived params: UPPERCASE (e.g., R_INNER, PITCH_CYLINDER)
        """
        from critbuddy.core.materials import get_density

        # =====================================================================
        # CYLINDER DIMENSIONS
        # =====================================================================
        R_inner = p["R_inner_cm"]
        H_inner = p["H_inner_cm"]
        t_wall = p["t_wall_cm"]

        R_outer = R_inner + t_wall
        H_outer = H_inner + 2 * t_wall  # top and bottom caps

        # =====================================================================
        # PACK DIMENSIONS
        # =====================================================================
        i = p["i"]
        j = p["j"]
        k = p["k"]
        gap_xy = p.get("gap_xy_cm", 0.0)
        gap_z = p.get("gap_z_cm", 0.0)

        # Pitch = center-to-center distance
        pitch_cylinder = 2 * R_outer + gap_xy
        pitch_z = H_outer + gap_z  # vertical spacing

        # Pack outer dimensions
        cassette_x = i * (2 * R_outer) + (i - 1) * gap_xy
        cassette_y = j * (2 * R_outer) + (j - 1) * gap_xy
        cassette_z = k * H_outer + (k - 1) * gap_z

        # =====================================================================
        # PACK DIMENSIONS
        # =====================================================================
        array_x = cassette_x
        array_y = cassette_y
        array_z = cassette_z

        # =====================================================================
        # TOTAL DIMENSIONS (depends on boundary condition)
        # =====================================================================
        boundary_type = p.get("boundary_type", "vacuum")
        reflector_thickness_input = p["reflector_thickness_cm"]

        if boundary_type == "reflective":
            # Reflective boundaries are placed at half-gap from the outer walls.
            reflector_thickness = 0.0
            total_x = array_x + gap_xy
            total_y = array_y + gap_xy
            total_z = array_z + gap_z
        else:
            reflector_thickness = reflector_thickness_input
            total_x = array_x + 2 * reflector_thickness
            total_y = array_y + 2 * reflector_thickness
            total_z = array_z + 2 * reflector_thickness

        # =====================================================================
        # MATERIAL PROPERTIES
        # =====================================================================
        wall_density = get_density(p["wall_material"])
        environment_material = p.get("environment_material", "humid_air")
        environment_density = p.get("environment_density")
        env_density = (
            environment_density
            if environment_density is not None
            else get_density(environment_material)
        )

        return {
            # Cylinder
            "R_INNER": R_inner,
            "R_OUTER": R_outer,
            "H_INNER": H_inner,
            "H_OUTER": H_outer,
            "T_WALL": t_wall,
            "WALL_MATERIAL": p["wall_material"],
            "WALL_DENSITY": wall_density,
            # Pack
            "I": i,
            "J": j,
            "K": k,
            "GAP_XY": gap_xy,
            "GAP_Z": gap_z,
            "PITCH_CYLINDER": pitch_cylinder,
            "PITCH_Z": pitch_z,
            "CASSETTE_X": cassette_x,
            "CASSETTE_Y": cassette_y,
            "CASSETTE_Z": cassette_z,
            "CYLINDERS_PER_PACK": i * j * k,
            # Pack
            "ARRAY_X": array_x,
            "ARRAY_Y": array_y,
            "ARRAY_Z": array_z,
            # Total
            "REFLECTOR_THICKNESS": reflector_thickness,
            "REFLECTOR_THICKNESS_INPUT": reflector_thickness_input,
            "TOTAL_X": total_x,
            "TOTAL_Y": total_y,
            "TOTAL_Z": total_z,
            "BOUNDARY_TYPE": boundary_type,
            # Counts
            "TOTAL_CYLINDERS": i * j * k,
            # Materials
            "ENRICHMENT": p["enrichment"],
            "FISSILE_MATERIAL": p["fissile_material"],
            "FISSILE_DENSITY": p.get("fissile_density"),
            "H_TO_U": p.get("h_to_u", 0.0),
            "ENVIRONMENT_MATERIAL": environment_material,
            "ENV_DENSITY": env_density,
        }


# Export the template class
Template = CascadeArrayTemplate
