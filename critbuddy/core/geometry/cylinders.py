"""
UF6 Shipping Cylinder Specifications Registry.

Standard cylinder dimensions per ANSI N14.1 and DOE specifications.
Provides a single source of truth for cylinder geometry, similar to the
materials registry pattern.

Usage:
    from critbuddy.core.geometry.cylinders import get_cylinder, get_inner_radius

    spec = get_cylinder("30b")
    print(spec.outer_diameter_cm)  # 76.2

    r_inner = get_inner_radius("30b")  # 37.30625
"""

from dataclasses import dataclass


@dataclass
class CylinderSpec:
    """Specification for a UF6 shipping/storage cylinder."""

    name: str
    outer_diameter_cm: float
    wall_thickness_cm: float
    internal_height_cm: float
    wall_material: str
    max_fill_kg: float
    tare_weight_kg: float
    description: str


CYLINDER_REGISTRY = {
    "1s": CylinderSpec(
        name="1S Cylinder",
        outer_diameter_cm=20.32,
        wall_thickness_cm=0.635,
        internal_height_cm=25.4,
        wall_material="steel",
        max_fill_kg=1.0,
        tare_weight_kg=8.0,
        description="Sample cylinder for HEU",
    ),
    "2s": CylinderSpec(
        name="2S Cylinder",
        outer_diameter_cm=12.7,
        wall_thickness_cm=0.635,
        internal_height_cm=40.64,
        wall_material="steel",
        max_fill_kg=2.2,
        tare_weight_kg=6.0,
        description="Sample cylinder for HEU",
    ),
    "5a": CylinderSpec(
        name="5A Cylinder",
        outer_diameter_cm=12.7,
        wall_thickness_cm=0.635,
        internal_height_cm=63.5,
        wall_material="steel",
        max_fill_kg=25.0,
        tare_weight_kg=25.0,
        description="Small sample cylinder for HALEU (up to 100% enrichment)",
    ),
    "5b": CylinderSpec(
        name="5B Cylinder",
        outer_diameter_cm=12.7,
        wall_thickness_cm=0.635,
        internal_height_cm=84.0,
        wall_material="steel",
        max_fill_kg=25.0,
        tare_weight_kg=27.0,
        description="Small sample cylinder for HALEU (up to 100% enrichment)",
    ),
    "30b": CylinderSpec(
        name="30B Cylinder",
        outer_diameter_cm=76.2,
        wall_thickness_cm=0.79375,
        internal_height_cm=170.0,
        wall_material="steel",
        max_fill_kg=2277.0,
        tare_weight_kg=635.0,
        description="HALEU transport cylinder (up to 20% enrichment)",
    ),
    "48x": CylinderSpec(
        name="48X Cylinder",
        outer_diameter_cm=121.92,
        wall_thickness_cm=1.27,
        internal_height_cm=302.26,
        wall_material="steel",
        max_fill_kg=9539.0,
        tare_weight_kg=1814.0,
        description="Large storage cylinder (up to 5% enrichment)",
    ),
    "48y": CylinderSpec(
        name="48Y Cylinder",
        outer_diameter_cm=121.92,
        wall_thickness_cm=1.5875,
        internal_height_cm=302.26,
        wall_material="steel",
        max_fill_kg=12501.0,
        tare_weight_kg=2041.0,
        description="Large LEU transport cylinder (up to 5% enrichment)",
    ),
    "48g": CylinderSpec(
        name="48G Cylinder",
        outer_diameter_cm=121.92,
        wall_thickness_cm=1.5875,
        internal_height_cm=302.26,
        wall_material="steel",
        max_fill_kg=12501.0,
        tare_weight_kg=2359.0,
        description="Large transport cylinder with lifting attachments",
    ),
}


def get_cylinder(cylinder_type: str) -> CylinderSpec:
    """Get cylinder specification by type name."""
    key = cylinder_type.lower()
    if key not in CYLINDER_REGISTRY:
        available = list(CYLINDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown cylinder type: '{cylinder_type}'. Available: {available}"
        )
    return CYLINDER_REGISTRY[key]


def get_inner_radius(cylinder_type: str) -> float:
    """Get inner radius in cm for a cylinder type."""
    spec = get_cylinder(cylinder_type)
    return (spec.outer_diameter_cm / 2.0) - spec.wall_thickness_cm


def get_inner_diameter(cylinder_type: str) -> float:
    """Get inner diameter in cm for a cylinder type."""
    return 2.0 * get_inner_radius(cylinder_type)


def get_internal_volume(cylinder_type: str) -> float:
    """Get internal volume in liters for a cylinder type."""
    import math

    spec = get_cylinder(cylinder_type)
    r_inner = get_inner_radius(cylinder_type)
    volume_cm3 = math.pi * r_inner**2 * spec.internal_height_cm
    return volume_cm3 / 1000.0


def list_cylinders() -> list[str]:
    """Return list of available cylinder types."""
    return list(CYLINDER_REGISTRY.keys())


def cylinder_info(cylinder_type: str) -> str:
    """Get formatted info string for a cylinder type."""
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
