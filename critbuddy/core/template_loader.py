"""
Helpers for loading template and model definitions from the filesystem.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from critbuddy.models.model_interface import OMCModel


def _default_templates_root() -> Path:
    return Path(__file__).resolve().parents[2] / "templates"


def _default_models_root() -> Path:
    return Path(__file__).resolve().parents[2] / "models"


def _load_definition_class(definition_name: str, definitions_root: Path):
    definition_init = definitions_root / definition_name / "__init__.py"
    module_name = definition_name.replace("-", "_")

    if not definition_init.exists():
        raise ValueError(f"Definition '{definition_name}' not found at {definition_init}")

    spec = importlib.util.spec_from_file_location(f"definitions.{module_name}", definition_init)
    if spec is None or spec.loader is None:
        raise ValueError(f"Failed loading definition module for '{definition_name}'")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "Template"):
        raise ValueError(f"Definition '{definition_name}' must export a 'Template' class")

    return module.Template()


def load_template_class(template_name: str, templates_root: Path | None = None):
    """Load template class by name from templates/<template_name>/__init__.py."""
    root = templates_root or _default_templates_root()
    return _load_definition_class(template_name, root)


def load_model_class(model_name: str, models_root: Path | None = None):
    """Load model definition class by name from models/<model_name>/__init__.py."""
    root = models_root or _default_models_root()
    return _load_definition_class(model_name, root)


def _load_definition_module(definition_dir: Path):
    """Load a definition module from openmc/model.py (or model.py fallback)."""
    template_path = definition_dir / "openmc" / "model.py"
    if not template_path.exists():
        template_path = definition_dir / "model.py"

    spec = importlib.util.spec_from_file_location("model", template_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Failed loading definition model from {template_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_template_module(template_dir: Path):
    """Load template model module from openmc/model.py (or model.py fallback)."""
    return _load_definition_module(template_dir)


def load_model_module(model_dir: Path):
    """Load a model module from models/<model_name>/openmc/model.py."""
    return _load_definition_module(model_dir)


class _LegacyModuleOMCModel(OMCModel):
    """Temporary adapter for legacy module-level OpenMC model functions."""

    def __init__(self, module):
        self._module = module

    def create_materials(self, params: dict):
        if not hasattr(self._module, "create_materials"):
            raise AttributeError("Legacy OpenMC module is missing create_materials(params)")
        return self._module.create_materials(params)

    def build_model(self, params: dict):
        return self._module.build_model(params)

    def create_settings(self, params: dict, dims: dict):
        return self._module.create_settings(params, dims)

    def create_plots(self, dims: dict, materials):
        return self._module.create_plots(dims, materials)


def _find_omc_model_classes(module) -> list[type[OMCModel]]:
    candidates: list[type[OMCModel]] = []
    for value in module.__dict__.values():
        if isinstance(value, type) and issubclass(value, OMCModel) and value is not OMCModel:
            candidates.append(value)
    return candidates


def load_openmc_model(definition_dir: Path) -> OMCModel:
    """Load a concrete OpenMC model implementation from `openmc/model.py`."""
    module = _load_definition_module(definition_dir)
    candidates = _find_omc_model_classes(module)

    if len(candidates) == 1:
        return candidates[0]()

    if len(candidates) > 1:
        candidate_names = ", ".join(sorted(cls.__name__ for cls in candidates))
        raise ValueError(
            f"Multiple OMCModel implementations found in {definition_dir}: {candidate_names}"
        )

    required_functions = ("build_model", "create_settings", "create_plots")
    if all(hasattr(module, name) for name in required_functions):
        return _LegacyModuleOMCModel(module)

    raise ValueError(f"No OMCModel implementation found in {definition_dir}")
