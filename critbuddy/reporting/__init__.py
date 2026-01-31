"""Reporting utilities for crit-buddy."""

from .geometry import create_geometry_plot
from .plots import plot_keff
from .plot_spec import PlotSpec, auto_plot_spec, get_plot_spec
from .voxel import (
    VoxelData,
    generate_voxel_data,
    export_vti,
    view_interactive,
    create_voxel_plot,
    create_isometric_slices,
)

__all__ = [
    "create_geometry_plot",
    "plot_keff",
    "PlotSpec",
    "auto_plot_spec",
    "get_plot_spec",
    "VoxelData",
    "generate_voxel_data",
    "export_vti",
    "view_interactive",
    "create_voxel_plot",
    "create_isometric_slices",
]
