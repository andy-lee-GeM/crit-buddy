"""
30B UF6 Cylinder Problem Template.

Based on ORNL/TM-2021/2043: Analysis of Maximum Enrichments for 30B UF6 Cylinders.

Models a 30B UF6 transportation/storage cylinder with:
- Carbon steel cylinder (76.2 cm diameter)
- UF6 with HF impurities (99.5 wt% UF6 + 0.5 wt% HF)
- Water reflector
"""

from critbuddy.core.template import ProblemTemplate, ParameterSpec


class UF6_30BTemplate(ProblemTemplate):
    """
    30B UF6 cylinder for HALEU transportation/storage.

    Geometry per ORNL/TM-2021/2043:
        - Cylinder: 76.2 cm diameter, carbon steel wall
        - Wall thickness: 0.79375 to 1.27 cm
        - UF6: 99.5 wt% UF6 + 0.5 wt% HF
        - Water reflector
    """

    PARAMETERS = {
        # Fissile Material
        "enrichment": ParameterSpec(
            type="float",
            default=10.0,
            min=0.7,
            max=20.0,
            unit="wt%",
            description="U-235 enrichment (weight percent, max 20% for HALEU)",
        ),
        "uf6_density": ParameterSpec(
            type="float",
            default=3.5,
            min=2.5,
            max=5.5,
            unit="g/cc",
            description="UF6 density (2.5-5.5 g/cm³ per ORNL analysis)",
        ),

        # 30B Cylinder Geometry (per ORNL/TM-2021/2043)
        # Outer diameter: 30 in (76.2 cm), Min wall: 5/16 in (0.79375 cm)
        # Inner radius = 38.1 - 0.79375 = 37.30625 cm
        # Min volume: 0.736 m³ → internal height ~170 cm
        "cylinder_radius_cm": ParameterSpec(
            type="float",
            default=37.30625,  # Inner radius = (76.2 cm OD)/2 - 0.79375 cm wall
            min=35.0,
            max=40.0,
            unit="cm",
            description="Inner radius of 30B cylinder (37.3 cm with min wall)",
        ),
        "cylinder_height_cm": ParameterSpec(
            type="float",
            default=170.0,  # Internal cavity height for 0.736 m³ min volume
            min=50.0,
            max=200.0,
            unit="cm",
            description="Internal cavity height of 30B cylinder",
        ),
        "wall_thickness_cm": ParameterSpec(
            type="float",
            default=0.79375,  # 5/16 inch minimum
            min=0.79375,
            max=1.27,  # 1/2 inch maximum
            unit="cm",
            description="Carbon steel wall thickness (5/16\" to 1/2\")",
        ),

        # Reflector
        "reflector_material": ParameterSpec(
            type="enum",
            options=["water", "none"],
            default="water",
            description="External reflector material",
        ),
        "reflector_thickness_cm": ParameterSpec(
            type="float",
            default=30.0,
            min=0.0,
            max=100.0,
            unit="cm",
            description="External reflector thickness (30 = full reflection)",
        ),
    }

    SIMULATION = {
        "PARTICLES": 10000,
        "BATCHES": 200,
        "INACTIVE": 50,
    }

    SAFETY_LIMIT = 0.95

    def derive_params(self, p: dict) -> dict:
        """
        Compute geometry parameters from user inputs.

        Geometry layers (inside to outside):
        1. UF6 fissile region
        2. Carbon steel cylinder wall
        3. External reflector (optional)
        """
        from critbuddy.core.materials import get_density

        # Inner cylinder dimensions
        r_inner = p["cylinder_radius_cm"]
        h_inner = p["cylinder_height_cm"]
        wall_t = p["wall_thickness_cm"]

        # Build up radii from inside out
        r_wall_outer = r_inner + wall_t

        # External reflector
        refl_t = p["reflector_thickness_cm"]
        if p["reflector_material"] == "none":
            refl_t = 0.0
        r_refl_outer = r_wall_outer + refl_t

        # Z coordinates
        z_bottom = 0.0
        z_top = h_inner
        z_refl_bottom = -refl_t if refl_t > 0 else 0.0
        z_refl_top = h_inner + refl_t

        # Source position (center of UF6 region)
        ksrc_z = h_inner / 2.0

        # Material densities
        wall_density = get_density("carbon_steel")
        refl_density = get_density(p["reflector_material"]) if p["reflector_material"] != "none" else 0.0

        return {
            # Fissile material
            "ENRICHMENT": p["enrichment"],
            "UF6_DENSITY": p["uf6_density"],

            # Cylinder radii
            "R_INNER": r_inner,
            "R_WALL_OUTER": r_wall_outer,
            "R_REFL_OUTER": r_refl_outer,

            # Z coordinates
            "Z_BOTTOM": z_bottom,
            "Z_TOP": z_top,
            "Z_REFL_BOTTOM": z_refl_bottom,
            "Z_REFL_TOP": z_refl_top,
            "WALL_THICKNESS": wall_t,

            # Reflector
            "REFLECTOR_MATERIAL": p["reflector_material"],
            "REFL_THICKNESS": refl_t,

            # Densities
            "WALL_DENSITY": wall_density,
            "REFL_DENSITY": refl_density,

            # Height
            "HEIGHT_CM": h_inner,

            # Source
            "KSRC_Z": ksrc_z,
        }


# Export the template class
Template = UF6_30BTemplate
