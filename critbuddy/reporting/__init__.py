"""Reporting utilities for crit-buddy."""

from .data import StudyResults
from .tables import results_table, comparison_table, summary_table
from .plots import generate_all_parameter_plots, solver_comparison_plot
from .geometry import create_geometry_plot
from .report import generate_report, print_report, save_report

__all__ = [
    "StudyResults",
    "results_table",
    "comparison_table",
    "summary_table",
    "generate_all_parameter_plots",
    "solver_comparison_plot",
    "create_geometry_plot",
    "generate_report",
    "print_report",
    "save_report",
]
