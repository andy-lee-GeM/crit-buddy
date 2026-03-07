"""
Helpers for loading template classes and model modules.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _default_templates_root() -> Path:
    return Path(__file__).resolve().parents[2] / "templates"


def load_template_class(template_name: str, templates_root: Path | None = None):
    """Load template class by name from templates/<template_name>/__init__.py."""
    root = templates_root or _default_templates_root()
    template_init = root / template_name / "__init__.py"

    if not template_init.exists():
        raise ValueError(f"Template '{template_name}' not found at {template_init}")

    spec = importlib.util.spec_from_file_location(f"templates.{template_name}", template_init)
    if spec is None or spec.loader is None:
        raise ValueError(f"Failed loading template module for '{template_name}'")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "Template"):
        raise ValueError(f"Template '{template_name}' must export a 'Template' class")

    return module.Template()


def load_template_module(template_dir: Path):
    """Load template model module from openmc/model.py (or model.py fallback)."""
    template_path = template_dir / "openmc" / "model.py"
    if not template_path.exists():
        template_path = template_dir / "model.py"

    spec = importlib.util.spec_from_file_location("model", template_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Failed loading template model from {template_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
