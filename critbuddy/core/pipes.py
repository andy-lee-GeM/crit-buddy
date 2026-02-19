"""
Standard pipe specifications registry.

Provides pipe dimensions per ASME B36.10M / B36.19M Schedule 10/10S.
All dimensions in centimeters.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PipeSpec:
    """Specification for a standard pipe size."""

    name: str  # NPS designation (e.g., "1", "2", "1/4")
    outer_diameter_cm: float
    inner_diameter_cm: float
    wall_thickness_cm: float
    category: str  # "pigtail" or "cascade"
    description: str

    @property
    def outer_radius_cm(self) -> float:
        """Outer radius in cm."""
        return self.outer_diameter_cm / 2

    @property
    def inner_radius_cm(self) -> float:
        """Inner radius (fissile region) in cm."""
        return self.inner_diameter_cm / 2


# Pipe registry - Schedule 10/10S (thinnest standard schedule)
PIPE_REGISTRY: Dict[str, PipeSpec] = {
    # Pigtails (NPS < 1/2)
    "1/8": PipeSpec(
        name="1/8",
        outer_diameter_cm=1.029,
        inner_diameter_cm=0.780,
        wall_thickness_cm=0.124,
        category="pigtail",
        description="NPS 1/8 pigtail",
    ),
    "1/4": PipeSpec(
        name="1/4",
        outer_diameter_cm=1.372,
        inner_diameter_cm=1.041,
        wall_thickness_cm=0.165,
        category="pigtail",
        description="NPS 1/4 pigtail",
    ),
    "3/8": PipeSpec(
        name="3/8",
        outer_diameter_cm=1.715,
        inner_diameter_cm=1.384,
        wall_thickness_cm=0.165,
        category="pigtail",
        description="NPS 3/8 pigtail",
    ),
    # Cascade lines (NPS 1 through 8)
    "1": PipeSpec(
        name="1",
        outer_diameter_cm=3.340,
        inner_diameter_cm=2.786,
        wall_thickness_cm=0.277,
        category="cascade",
        description="NPS 1 cascade line",
    ),
    "1-1/4": PipeSpec(
        name="1-1/4",
        outer_diameter_cm=4.216,
        inner_diameter_cm=3.663,
        wall_thickness_cm=0.277,
        category="cascade",
        description="NPS 1-1/4 cascade line",
    ),
    "1-1/2": PipeSpec(
        name="1-1/2",
        outer_diameter_cm=4.826,
        inner_diameter_cm=4.272,
        wall_thickness_cm=0.277,
        category="cascade",
        description="NPS 1-1/2 cascade line",
    ),
    "2": PipeSpec(
        name="2",
        outer_diameter_cm=6.032,
        inner_diameter_cm=5.479,
        wall_thickness_cm=0.277,
        category="cascade",
        description="NPS 2 cascade line",
    ),
    "2-1/2": PipeSpec(
        name="2-1/2",
        outer_diameter_cm=7.303,
        inner_diameter_cm=6.693,
        wall_thickness_cm=0.305,
        category="cascade",
        description="NPS 2-1/2 cascade line",
    ),
    "3": PipeSpec(
        name="3",
        outer_diameter_cm=8.890,
        inner_diameter_cm=8.280,
        wall_thickness_cm=0.305,
        category="cascade",
        description="NPS 3 cascade line",
    ),
    "3-1/2": PipeSpec(
        name="3-1/2",
        outer_diameter_cm=10.160,
        inner_diameter_cm=9.550,
        wall_thickness_cm=0.305,
        category="cascade",
        description="NPS 3-1/2 cascade line",
    ),
    "4": PipeSpec(
        name="4",
        outer_diameter_cm=11.430,
        inner_diameter_cm=10.820,
        wall_thickness_cm=0.305,
        category="cascade",
        description="NPS 4 cascade line",
    ),
    "5": PipeSpec(
        name="5",
        outer_diameter_cm=14.130,
        inner_diameter_cm=13.449,
        wall_thickness_cm=0.340,
        category="cascade",
        description="NPS 5 cascade line",
    ),
    "6": PipeSpec(
        name="6",
        outer_diameter_cm=16.828,
        inner_diameter_cm=16.147,
        wall_thickness_cm=0.340,
        category="cascade",
        description="NPS 6 cascade line",
    ),
    "8": PipeSpec(
        name="8",
        outer_diameter_cm=21.908,
        inner_diameter_cm=21.156,
        wall_thickness_cm=0.376,
        category="cascade",
        description="NPS 8 cascade line",
    ),
}

# Aliases for common naming conventions
PIPE_ALIASES = {
    "nps1/8": "1/8",
    "nps1/4": "1/4",
    "nps3/8": "3/8",
    "nps1": "1",
    "nps1-1/4": "1-1/4",
    "nps1-1/2": "1-1/2",
    "nps2": "2",
    "nps2-1/2": "2-1/2",
    "nps3": "3",
    "nps3-1/2": "3-1/2",
    "nps4": "4",
    "nps5": "5",
    "nps6": "6",
    "nps8": "8",
    # Numeric aliases
    "0.125": "1/8",
    "0.25": "1/4",
    "0.375": "3/8",
    "1.0": "1",
    "1.25": "1-1/4",
    "1.5": "1-1/2",
    "2.0": "2",
    "2.5": "2-1/2",
    "3.0": "3",
    "3.5": "3-1/2",
    "4.0": "4",
    "5.0": "5",
    "6.0": "6",
    "8.0": "8",
}


def get_pipe(pipe_size: str) -> PipeSpec:
    """
    Get pipe specification by NPS size.

    Args:
        pipe_size: NPS designation (e.g., "2", "1-1/4", "nps2")

    Returns:
        PipeSpec for the requested size

    Raises:
        ValueError: If pipe size not found
    """
    # Normalize input
    key = pipe_size.lower().strip()

    # Check aliases first
    if key in PIPE_ALIASES:
        key = PIPE_ALIASES[key]

    # Look up in registry
    if key in PIPE_REGISTRY:
        return PIPE_REGISTRY[key]

    # Try without fractions
    available = ", ".join(sorted(PIPE_REGISTRY.keys()))
    raise ValueError(
        f"Unknown pipe size: '{pipe_size}'. "
        f"Available sizes: {available}"
    )


def get_inner_radius(pipe_size: str) -> float:
    """Get inner radius (fissile region) for a pipe size."""
    return get_pipe(pipe_size).inner_radius_cm


def get_outer_radius(pipe_size: str) -> float:
    """Get outer radius for a pipe size."""
    return get_pipe(pipe_size).outer_radius_cm


def get_wall_thickness(pipe_size: str) -> float:
    """Get wall thickness for a pipe size."""
    return get_pipe(pipe_size).wall_thickness_cm


def list_pipes(category: Optional[str] = None) -> list:
    """
    List available pipe sizes.

    Args:
        category: Optional filter - "pigtail" or "cascade"

    Returns:
        List of (nps, description) tuples
    """
    result = []
    for nps, spec in PIPE_REGISTRY.items():
        if category is None or spec.category == category:
            result.append((nps, spec.description))
    return result
