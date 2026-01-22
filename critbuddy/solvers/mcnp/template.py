"""
Simple template engine for MCNP input file generation.

Replaces {{PARAM}} placeholders with values from a dictionary.
"""

import re
from pathlib import Path


def render(template: str, params: dict) -> str:
    """
    Replace {{PARAM}} placeholders with values.

    Args:
        template: Template string with {{PARAM}} placeholders
        params: Dictionary of parameter name -> value

    Returns:
        Rendered string with placeholders replaced
    """
    def replace(match):
        key = match.group(1)
        if key not in params:
            raise ValueError(f"Missing parameter: {key}")
        value = params[key]
        # Format floats with reasonable precision
        if isinstance(value, float):
            return f"{value:.6f}"
        return str(value)

    pattern = re.compile(r"\{\{(\w+)\}\}")
    return pattern.sub(replace, template)


def render_file(template_path: Path, params: dict, output_path: Path) -> None:
    """
    Render a template file and write output.

    Args:
        template_path: Path to template file
        params: Dictionary of parameter values
        output_path: Path for rendered output
    """
    template = Path(template_path).read_text()
    content = render(template, params)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content)
