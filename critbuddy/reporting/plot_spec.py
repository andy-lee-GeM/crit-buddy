"""
Plot specification for 3D visualization.

Decouples geometry knowledge from rendering logic. Templates can optionally
provide custom PlotSpec, otherwise auto-computed from geometry bounding box.
"""

from dataclasses import dataclass, field
from typing import Tuple, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import openmc


@dataclass
class PlotSpec:
    """Camera and framing parameters for 3D visualization."""

    center: Tuple[float, float, float]
    """Point the camera looks at (x, y, z) in cm."""

    width: Tuple[float, float, float]
    """Size of the viewing region (x, y, z) in cm."""

    up_axis: str = "z"
    """Which axis points up: 'x', 'y', or 'z'."""

    exclude_materials: List[str] = field(default_factory=lambda: ["Air", "Water"])
    """Materials to hide (so you can see inside)."""


def auto_plot_spec(geometry: "openmc.Geometry", padding: float = 1.1) -> PlotSpec:
    """
    Compute PlotSpec automatically from geometry bounding box.

    Works for any OpenMC geometry without template-specific knowledge.

    Args:
        geometry: OpenMC Geometry object
        padding: Multiplier for width (1.1 = 10% padding)

    Returns:
        PlotSpec with auto-computed center and width
    """
    bbox = geometry.bounding_box
    lower, upper = bbox

    center = (
        (lower[0] + upper[0]) / 2,
        (lower[1] + upper[1]) / 2,
        (lower[2] + upper[2]) / 2,
    )

    width = (
        (upper[0] - lower[0]) * padding,
        (upper[1] - lower[1]) * padding,
        (upper[2] - lower[2]) * padding,
    )

    return PlotSpec(center=center, width=width)


def get_plot_spec(
    geometry: "openmc.Geometry",
    template=None,
    dims: Optional[dict] = None,
) -> PlotSpec:
    """
    Get PlotSpec, preferring template-provided if available.

    Args:
        geometry: OpenMC Geometry object
        template: Optional ProblemTemplate instance
        dims: Optional dims dict from build_model()

    Returns:
        PlotSpec from template or auto-computed
    """
    # Template override
    if template is not None and dims is not None:
        if hasattr(template, "get_plot_spec"):
            return template.get_plot_spec(dims)

    # Auto-compute fallback
    return auto_plot_spec(geometry)
