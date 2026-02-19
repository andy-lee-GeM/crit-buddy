"""
Base class for problem templates.

Templates define the physics problem: geometry, materials, and parameter schema.
Engineers use templates by specifying physical parameters; templates handle
all derived calculations and simulation settings.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ParameterSpec:
    """Schema specification for a single parameter."""

    type: str  # "float", "int", "enum"
    required: bool = False
    default: Any = None
    options: List[str] = None  # For enum type
    min: float = None
    max: float = None
    unit: str = None
    description: str = ""


class ProblemTemplate(ABC):
    """
    Base class for all problem templates.

    Subclasses define:
    - PARAMETERS: Schema for user-facing parameters
    - SIMULATION: Fixed simulation settings (particles, batches, etc.)
    - SAFETY_LIMIT: k-eff threshold for safety classification
    - derive_params(): Compute geometry/physics params from user inputs
    """

    # Subclasses override these
    PARAMETERS: Dict[str, ParameterSpec] = {}
    SIMULATION: Dict[str, int] = {
        "PARTICLES": 10000,
        "BATCHES": 150,
        "INACTIVE": 50,
    }
    SAFETY_LIMIT: float = 0.95

    @abstractmethod
    def derive_params(self, user_params: dict) -> dict:
        """
        Compute derived parameters from user inputs.

        This is where templates compute geometry parameters (R1, R2, R3,
        Z coordinates, etc.) from user-specified physical parameters
        (radius_cm, height_cm, wall_thickness_cm, etc.).

        Args:
            user_params: Dictionary of user-provided parameter values

        Returns:
            Dictionary of derived parameters to merge with user params
        """
        pass

    def validate_params(self, user_params: dict) -> List[str]:
        """
        Validate user parameters against schema.

        Args:
            user_params: Dictionary of user-provided values

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        for name, spec in self.PARAMETERS.items():
            value = user_params.get(name)

            # Check required
            if spec.required and value is None:
                errors.append(f"Required parameter '{name}' is missing")
                continue

            if value is None:
                continue

            # Handle list (sweep) - validate each element
            values = value if isinstance(value, list) else [value]

            for v in values:
                # Type checking
                if spec.type == "float" and not isinstance(v, (int, float)):
                    errors.append(f"Parameter '{name}' must be a number, got {type(v).__name__}")
                elif spec.type == "int" and not isinstance(v, int):
                    errors.append(f"Parameter '{name}' must be an integer, got {type(v).__name__}")
                elif spec.type == "enum" and v not in spec.options:
                    errors.append(f"Parameter '{name}' must be one of {spec.options}, got '{v}'")

                # Range checking for numeric types
                if spec.type in ("float", "int") and isinstance(v, (int, float)):
                    if spec.min is not None and v < spec.min:
                        errors.append(f"Parameter '{name}' value {v} below minimum {spec.min}")
                    if spec.max is not None and v > spec.max:
                        errors.append(f"Parameter '{name}' value {v} above maximum {spec.max}")

        # Check for unknown parameters
        known_params = set(self.PARAMETERS.keys())
        for name in user_params:
            if name not in known_params and name not in ("problem", "name", "solvers"):
                errors.append(f"Unknown parameter '{name}'")

        return errors

    def apply_defaults(self, user_params: dict) -> dict:
        """
        Apply default values for missing optional parameters.

        Args:
            user_params: Dictionary of user-provided values

        Returns:
            New dictionary with defaults filled in
        """
        result = dict(user_params)

        for name, spec in self.PARAMETERS.items():
            if name not in result and spec.default is not None:
                result[name] = spec.default

        return result

    def get_simulation_params(self) -> dict:
        """Get simulation parameters (can be overridden for smoke tests)."""
        return dict(self.SIMULATION)
