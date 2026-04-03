"""
Solver backends for criticality calculations.

Provides a unified interface for running simulations with different
Monte Carlo codes (OpenMC, MCNP).
"""

from .base import Solver, SolverResult, compute_status

__all__ = ["Solver", "SolverResult", "compute_status", "OpenMCSolver", "MCNPSolver"]


def __getattr__(name: str):
    if name == "OpenMCSolver":
        from .openmc.solver import OpenMCSolver

        return OpenMCSolver
    if name == "MCNPSolver":
        from .mcnp.solver import MCNPSolver

        return MCNPSolver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
