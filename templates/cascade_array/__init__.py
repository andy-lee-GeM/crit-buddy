"""
Cascade Array Problem Template.

A hierarchical array of cylinders organized as:
    - Cylinders within cassettes (i x j x k lattice)
    - Cassettes within rows (M cassettes per row)
    - 2 rows forming the complete cascade

Geometry Hierarchy:
    Level 1: Cylinder    - Single steel-clad vessel with fissile material
    Level 2: Cassette    - i x j x k lattice of cylinders
    Level 3: Row         - M cassettes in a line along X
    Level 4: Cascade     - 2 rows + water reflector (ROOT)

Applications: Cascade hall layouts, process equipment arrays
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class CascadeArrayTemplate(ProblemTemplate):
    """
    Cascade array template with nested universe hierarchy.

    Coordinate system:
        - X: cassette direction within row (M cassettes)
        - Y: row direction (2 rows)
        - Z: vertical (k layers within cassette)
        - Origin at corner of array (not centered)
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
            default=5.09,
            min=1.0,
            max=7.0,
            unit="g/cc",
            description="Fissile material density (UF6: 5.09, UO2F2: 6.37)",
        ),
        "h_to_u_ratio": ParameterSpec(
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
        # CASSETTE CONFIGURATION (i x j x k cylinders)
        # =====================================================================
        "i": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=20,
            description="Cylinders per cassette in X direction",
        ),
        "j": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=20,
            description="Cylinders per cassette in Y direction",
        ),
        "k": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=10,
            description="Cylinders per cassette in Z direction (layers)",
        ),
        "d_cylinder_cm": ParameterSpec(
            type="float",
            required=True,
            min=0.0,
            max=100.0,
            unit="cm",
            description="Gap between cylinder outer walls within cassette",
        ),
        # =====================================================================
        # ROW CONFIGURATION (M cassettes)
        # =====================================================================
        "M": ParameterSpec(
            type="int",
            required=True,
            min=1,
            max=50,
            description="Number of cassettes per row",
        ),
        "d_cassette_cm": ParameterSpec(
            type="float",
            required=True,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Gap between cassettes within a row",
        ),
        # =====================================================================
        # CASCADE CONFIGURATION (2 rows)
        # =====================================================================
        "d_row_cm": ParameterSpec(
            type="float",
            required=True,
            min=0.0,
            max=200.0,
            unit="cm",
            description="Gap between the two rows",
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
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=5.0,
            max=100.0,
            unit="cm",
            description="Water reflector thickness around cascade",
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
        # CASSETTE DIMENSIONS
        # =====================================================================
        i = p["i"]
        j = p["j"]
        k = p["k"]
        d_cylinder = p["d_cylinder_cm"]

        # Pitch = center-to-center distance
        pitch_cylinder = 2 * R_outer + d_cylinder
        pitch_z = H_outer + d_cylinder  # vertical spacing

        # Cassette outer dimensions
        cassette_x = i * pitch_cylinder
        cassette_y = j * pitch_cylinder
        cassette_z = k * pitch_z

        # =====================================================================
        # ROW DIMENSIONS
        # =====================================================================
        M = p["M"]
        d_cassette = p["d_cassette_cm"]

        pitch_cassette = cassette_x + d_cassette
        row_x = M * pitch_cassette

        # =====================================================================
        # CASCADE DIMENSIONS
        # =====================================================================
        d_row = p["d_row_cm"]

        pitch_row = cassette_y + d_row
        array_x = row_x
        array_y = 2 * pitch_row  # 2 rows
        array_z = cassette_z

        # =====================================================================
        # TOTAL DIMENSIONS (with reflector)
        # =====================================================================
        reflector_thickness = p["reflector_thickness_cm"]

        total_x = array_x + 2 * reflector_thickness
        total_y = array_y + 2 * reflector_thickness
        total_z = array_z + 2 * reflector_thickness

        # =====================================================================
        # MATERIAL PROPERTIES
        # =====================================================================
        wall_density = get_density(p["wall_material"])

        return {
            # Cylinder
            "R_INNER": R_inner,
            "R_OUTER": R_outer,
            "H_INNER": H_inner,
            "H_OUTER": H_outer,
            "T_WALL": t_wall,
            "WALL_MATERIAL": p["wall_material"],
            "WALL_DENSITY": wall_density,
            # Cassette
            "I": i,
            "J": j,
            "K": k,
            "D_CYLINDER": d_cylinder,
            "PITCH_CYLINDER": pitch_cylinder,
            "PITCH_Z": pitch_z,
            "CASSETTE_X": cassette_x,
            "CASSETTE_Y": cassette_y,
            "CASSETTE_Z": cassette_z,
            "CYLINDERS_PER_CASSETTE": i * j * k,
            # Row
            "M": M,
            "D_CASSETTE": d_cassette,
            "PITCH_CASSETTE": pitch_cassette,
            "ROW_X": row_x,
            # Cascade
            "D_ROW": d_row,
            "PITCH_ROW": pitch_row,
            "ARRAY_X": array_x,
            "ARRAY_Y": array_y,
            "ARRAY_Z": array_z,
            # Total
            "REFLECTOR_THICKNESS": reflector_thickness,
            "TOTAL_X": total_x,
            "TOTAL_Y": total_y,
            "TOTAL_Z": total_z,
            # Counts
            "CASSETTES_PER_ROW": M,
            "TOTAL_CASSETTES": 2 * M,
            "TOTAL_CYLINDERS": 2 * M * i * j * k,
            # Materials
            "ENRICHMENT": p["enrichment"],
            "FISSILE_MATERIAL": p["fissile_material"],
            "FISSILE_DENSITY": p["fissile_density"],
            "H_TO_U_RATIO": p.get("h_to_u_ratio", 0.0),
            "ENVIRONMENT_MATERIAL": p["environment_material"],
        }


# Export the template class
Template = CascadeArrayTemplate
