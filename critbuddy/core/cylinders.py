"""
UF6 Shipping Cylinder Specifications Registry.

Standard cylinder dimensions per ANSI N14.1 and DOE specifications.
Provides a single source of truth for cylinder geometry, similar to the
materials registry pattern.

Usage:
    from critbuddy.core.cylinders import get_cylinder, get_inner_radius

    spec = get_cylinder("30b")
    print(spec.outer_diameter_cm)  # 76.2

    r_inner = get_inner_radius("30b")  # 37.30625
"""

from dataclasses import dataclass


@dataclass
class CylinderSpec:
    """Specification for a UF6 shipping/storage cylinder."""

    name: str                    # Human-readable name
    outer_diameter_cm: float     # Outer diameter
    wall_thickness_cm: float     # Minimum wall thickness
    internal_height_cm: float    # Internal cavity height
    wall_material: str           # Reference to material registry key
    max_fill_kg: float           # Maximum UF6 fill weight
    tare_weight_kg: float        # Empty cylinder weight
    description: str             # Usage description


# =============================================================================
# CYLINDER REGISTRY
# =============================================================================

CYLINDER_REGISTRY = {
    # Small cylinders
    "1s": CylinderSpec(
        name="1S Cylinder",
        outer_diameter_cm=20.32,      # 8 inch OD
        wall_thickness_cm=0.635,      # 1/4 inch
        internal_height_cm=25.4,      # ~10 inches
        wall_material="steel",
        max_fill_kg=1.0,
        tare_weight_kg=8.0,
        description="Sample cylinder for HEU",
    ),
    "2s": CylinderSpec(
        name="2S Cylinder",
        outer_diameter_cm=12.7,       # 5 inch OD
        wall_thickness_cm=0.635,      # 1/4 inch
        internal_height_cm=40.64,     # ~16 inches
        wall_material="steel",
        max_fill_kg=2.2,
        tare_weight_kg=6.0,
        description="Sample cylinder for HEU",
    ),
    "5a": CylinderSpec(
        name="5A Cylinder",
        outer_diameter_cm=12.7,       # 5 inch OD
        wall_thickness_cm=0.635,      # 1/4 inch
        internal_height_cm=63.5,      # ~25 inches
        wall_material="steel",
        max_fill_kg=25.0,
        tare_weight_kg=25.0,
        description="Small sample cylinder for HALEU (up to 100% enrichment)",
    ),
    "5b": CylinderSpec(
        name="5B Cylinder",
        outer_diameter_cm=12.7,       # 5 inch OD
        wall_thickness_cm=0.635,      # 1/4 inch
        internal_height_cm=84.0,      # ~33 inches
        wall_material="steel",
        max_fill_kg=25.0,
        tare_weight_kg=27.0,
        description="Small sample cylinder for HALEU (up to 100% enrichment)",
    ),

    # Medium cylinders
    "30b": CylinderSpec(
        name="30B Cylinder",
        outer_diameter_cm=76.2,       # 30 inch OD
        wall_thickness_cm=0.79375,    # 5/16 inch minimum
        internal_height_cm=170.0,     # Per ORNL/TM-2021/2043
        wall_material="steel",
        max_fill_kg=2277.0,
        tare_weight_kg=635.0,
        description="HALEU transport cylinder (up to 20% enrichment)",
    ),

    # Large cylinders
    "48x": CylinderSpec(
        name="48X Cylinder",
        outer_diameter_cm=121.92,     # 48 inch OD
        wall_thickness_cm=1.27,       # 1/2 inch
        internal_height_cm=302.26,    # ~119 inches
        wall_material="steel",
        max_fill_kg=9539.0,
        tare_weight_kg=1814.0,
        description="Large storage cylinder (up to 5% enrichment)",
    ),
    "48y": CylinderSpec(
        name="48Y Cylinder",
        outer_diameter_cm=121.92,     # 48 inch OD
        wall_thickness_cm=1.5875,     # 5/8 inch
        internal_height_cm=302.26,    # ~119 inches
        wall_material="steel",
        max_fill_kg=12501.0,
        tare_weight_kg=2041.0,
        description="Large LEU transport cylinder (up to 5% enrichment)",
    ),
    "48g": CylinderSpec(
        name="48G Cylinder",
        outer_diameter_cm=121.92,     # 48 inch OD
        wall_thickness_cm=1.5875,     # 5/8 inch
        internal_height_cm=302.26,    # ~119 inches
        wall_material="steel",
        max_fill_kg=12501.0,
        tare_weight_kg=2359.0,
        description="Large transport cylinder with lifting attachments",
    ),
}


# =============================================================================
# ACCESSOR FUNCTIONS
# =============================================================================

def get_cylinder(cylinder_type: str) -> CylinderSpec:
    """
    Get cylinder specification by type name.

    Args:
        cylinder_type: Cylinder designation (e.g., "30b", "5a", "48y")

    Returns:
        CylinderSpec with all dimensions and properties

    Raises:
        ValueError: If cylinder type not found in registry
    """
    key = cylinder_type.lower()
    if key not in CYLINDER_REGISTRY:
        available = list(CYLINDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown cylinder type: '{cylinder_type}'. Available: {available}"
        )
    return CYLINDER_REGISTRY[key]


def get_inner_radius(cylinder_type: str) -> float:
    """
    Get inner radius in cm for a cylinder type.

    Args:
        cylinder_type: Cylinder designation (e.g., "30b")

    Returns:
        Inner radius in cm (outer_diameter/2 - wall_thickness)
    """
    spec = get_cylinder(cylinder_type)
    return (spec.outer_diameter_cm / 2.0) - spec.wall_thickness_cm


def get_inner_diameter(cylinder_type: str) -> float:
    """
    Get inner diameter in cm for a cylinder type.

    Args:
        cylinder_type: Cylinder designation (e.g., "30b")

    Returns:
        Inner diameter in cm
    """
    return 2.0 * get_inner_radius(cylinder_type)


def get_internal_volume(cylinder_type: str) -> float:
    """
    Get internal volume in liters for a cylinder type.

    Args:
        cylinder_type: Cylinder designation (e.g., "30b")

    Returns:
        Internal volume in liters
    """
    import math
    spec = get_cylinder(cylinder_type)
    r_inner = get_inner_radius(cylinder_type)
    volume_cm3 = math.pi * r_inner**2 * spec.internal_height_cm
    return volume_cm3 / 1000.0  # Convert cm³ to liters


def list_cylinders() -> list[str]:
    """Return list of available cylinder types."""
    return list(CYLINDER_REGISTRY.keys())


def cylinder_info(cylinder_type: str) -> str:
    """
    Get formatted info string for a cylinder type.

    Args:
        cylinder_type: Cylinder designation

    Returns:
        Multi-line string with cylinder specifications
    """
    spec = get_cylinder(cylinder_type)
    r_inner = get_inner_radius(cylinder_type)
    volume = get_internal_volume(cylinder_type)

    return f"""{spec.name}
  Description: {spec.description}
  Outer diameter: {spec.outer_diameter_cm:.2f} cm ({spec.outer_diameter_cm/2.54:.1f} in)
  Wall thickness: {spec.wall_thickness_cm:.4f} cm ({spec.wall_thickness_cm/2.54:.3f} in)
  Inner radius: {r_inner:.4f} cm
  Internal height: {spec.internal_height_cm:.2f} cm
  Internal volume: {volume:.1f} L
  Wall material: {spec.wall_material}
  Max fill: {spec.max_fill_kg:.1f} kg
  Tare weight: {spec.tare_weight_kg:.1f} kg"""
