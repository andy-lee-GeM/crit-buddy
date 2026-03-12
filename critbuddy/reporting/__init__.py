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
from .ticket_report import generate_ticket_report
from .summary_plots import generate_summary_plots

__all__ = [
    "create_geometry_plot",
    "plot_keff",
    "plot_heatmap",
    "generate_report",
    "generate_calculation_report",
    "PlotSpec",
    "auto_plot_spec",
    "get_plot_spec",
    "VoxelData",
    "generate_voxel_data",
    "export_vti",
    "view_interactive",
    "create_voxel_plot",
    "create_isometric_slices",
    "generate_ticket_report",
    "generate_summary_plots",
]
