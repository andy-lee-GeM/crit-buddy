"""Reporting utilities for crit-buddy."""

from .geometry import create_geometry_plot
from .plots import plot_keff, plot_heatmap, plot_keff_vs_gap_by_enrichment
from .report import generate_report, generate_calculation_report
from .plot_spec import PlotSpec, auto_plot_spec, get_plot_spec
from .voxel import (
    VoxelData,
    generate_voxel_data,
    export_vti,
    view_interactive,
    create_voxel_plot,
    create_isometric_slices,
)
from .excel import generate_lookup_xlsx, generate_cascade_array_xlsx

__all__ = [
    "create_geometry_plot",
    "plot_keff",
    "plot_heatmap",
    "generate_report",
    "generate_calculation_report",
    "generate_lookup_xlsx",
    "generate_cascade_array_xlsx",
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
