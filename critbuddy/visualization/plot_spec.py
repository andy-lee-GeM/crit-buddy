"""
Plot specification for 3D visualization.

Decouples geometry knowledge from rendering logic. Templates can optionally
provide custom PlotSpec, otherwise auto-computed from geometry bounding box.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    import openmc


@dataclass
class PlotSpec:
    """Camera and framing parameters for 3D visualization."""

    center: Tuple[float, float, float]
    width: Tuple[float, float, float]
    up_axis: str = "z"
    exclude_materials: List[str] = field(default_factory=lambda: ["Air", "Water"])
    max_resolution: int = 100


def auto_plot_spec(geometry: "openmc.Geometry", padding: float = 1.1) -> PlotSpec:
    """Compute PlotSpec automatically from geometry bounding box."""
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
    """Get PlotSpec, preferring a template-provided override."""
    if template is not None and dims is not None and hasattr(template, "get_plot_spec"):
        return template.get_plot_spec(dims)
    return auto_plot_spec(geometry)
