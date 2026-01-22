"""
Solver backends for criticality calculations.

Provides a unified interface for running simulations with different
Monte Carlo codes (OpenMC, MCNP).
"""

from .base import Solver, SolverResult, compute_status
from .openmc.solver import OpenMCSolver
from .mcnp.solver import MCNPSolver

__all__ = ["Solver", "SolverResult", "compute_status", "OpenMCSolver", "MCNPSolver"]
