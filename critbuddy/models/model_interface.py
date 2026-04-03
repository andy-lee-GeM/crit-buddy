"""Interface contract for OpenMC model implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class OMCModel(ABC):
    """Required callable surface for `models/<name>/openmc/model.py`."""

    @abstractmethod
    def create_materials(self, params: dict[str, Any]):
        """
        Create OpenMC materials for the model.

        Implementations may return additional material handles alongside the
        `openmc.Materials` collection when needed by `build_model()`.
        """

    @abstractmethod
    def build_model(self, params: dict[str, Any]):
        """
        Build the OpenMC model and return `(materials, geometry, dims)`.

        `params` is expected to be the fully derived parameter dictionary from
        the corresponding `Template` in `models/<name>/__init__.py`.
        """

    @abstractmethod
    def create_settings(self, params: dict[str, Any], dims: dict[str, Any]):
        """Create OpenMC settings for the model."""

    @abstractmethod
    def create_plots(self, dims: dict[str, Any], materials):
        """Create OpenMC geometry validation plots for the model."""
