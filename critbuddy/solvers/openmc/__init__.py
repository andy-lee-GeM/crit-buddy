"""OpenMC solver backend."""

from critbuddy.models.model_interface import OMCModel

__all__ = ["OMCModel", "OpenMCSolver"]


def __getattr__(name: str):
    if name == "OpenMCSolver":
        from .solver import OpenMCSolver

        return OpenMCSolver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
