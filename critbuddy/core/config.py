"""
Experiment configuration loader.

Handles the simplified engineer-facing config format where:
- Simple values are fixed parameters
- Lists are swept (cartesian product for multiple lists)
- Templates handle all derived parameters and simulation settings
"""

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ExperimentConfig:
    """Parsed experiment configuration."""

    problem: Optional[str]
    model: Optional[str]
    name: str
    user_params: Dict[str, Any]

    @property
    def definition_kind(self) -> str:
        """Whether this config resolves to a legacy problem template or a model."""
        return "model" if self.model else "problem"

    @property
    def definition_name(self) -> str:
        """Resolved model or problem name used for loading."""
        return self.model or self.problem or ""

    @classmethod
    def from_file(cls, path: Path) -> "ExperimentConfig":
        """Load experiment config from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "ExperimentConfig":
        """Create config from dictionary."""
        problem = data.get("problem")
        model = data.get("model")
        if not problem and not model:
            raise ValueError("Config must specify either 'problem' or 'model'")

        name = data.get("name", "Unnamed experiment")

        params = data.get("params")
        if params is not None and not isinstance(params, dict):
            raise ValueError("'params' must be a mapping when provided")

        # Everything else is a user parameter. Model configs can use nested
        # params while legacy problem configs keep the flat structure.
        reserved_keys = {"problem", "model", "name", "params", "solver", "solvers"}
        user_params = dict(params or {})
        user_params.update({k: v for k, v in data.items() if k not in reserved_keys})

        return cls(
            problem=problem,
            model=model,
            name=name,
            user_params=user_params,
        )


@dataclass
class Case:
    """A single simulation case with resolved parameters."""

    label: str
    user_params: Dict[str, Any]
    derived_params: Dict[str, Any] = field(default_factory=dict)
    simulation_params: Dict[str, Any] = field(default_factory=dict)

    @property
    def all_params(self) -> Dict[str, Any]:
        """Get all parameters merged for solver execution."""
        return {
            **self.user_params,
            **self.derived_params,
            **self.simulation_params,
        }


def expand_sweeps(user_params: dict) -> List[tuple]:
    """
    Expand list values into cartesian product of cases.

    Args:
        user_params: Dictionary where lists indicate sweep values

    Returns:
        List of (label, params_dict) tuples

    Example:
        >>> expand_sweeps({"radius_cm": [5, 10], "enrichment": 5.0})
        [("case_1", {"radius_cm": 5, "enrichment": 5.0}),
         ("case_2", {"radius_cm": 10, "enrichment": 5.0})]
    """
    # Identify swept vs fixed parameters
    swept = {}
    fixed = {}

    for key, value in user_params.items():
        if isinstance(value, list) and len(value) > 0:
            swept[key] = value
        else:
            fixed[key] = value

    # If no sweeps, return single case
    if not swept:
        return [("case_1", dict(fixed))]

    # Generate cartesian product of swept values
    sweep_keys = list(swept.keys())
    sweep_values = [swept[k] for k in sweep_keys]

    cases = []
    for case_num, combo in enumerate(itertools.product(*sweep_values), start=1):
        # Build params dict
        params = dict(fixed)

        for key, value in zip(sweep_keys, combo):
            params[key] = value

        label = f"case_{case_num}"
        cases.append((label, params))

    return cases


def generate_cases(
    config: ExperimentConfig,
    template: "ProblemTemplate",
    smoke_test: bool = False,
) -> List[Case]:
    """
    Generate all cases from experiment config and template.

    Args:
        config: Parsed experiment configuration
        template: Problem template instance
        smoke_test: If True, limit to 1 case with minimal simulation params

    Returns:
        List of Case objects ready for solver execution
    """
    # Validate user parameters
    errors = template.validate_params(config.user_params)
    if errors:
        raise ValueError(f"Invalid parameters:\n  " + "\n  ".join(errors))

    # Apply template defaults
    user_params = template.apply_defaults(config.user_params)

    # Expand sweeps
    sweep_cases = expand_sweeps(user_params)

    # Limit to first case for smoke test
    if smoke_test:
        sweep_cases = sweep_cases[:1]

    # Get simulation params (may be overridden for smoke test)
    if smoke_test:
        simulation_params = {"PARTICLES": 5000, "BATCHES": 50, "INACTIVE": 10}
    else:
        simulation_params = template.get_simulation_params()

    # Build Case objects
    cases = []
    for label, params in sweep_cases:
        # Template computes derived parameters
        derived = template.derive_params(params)

        cases.append(
            Case(
                label=label,
                user_params=params,
                derived_params=derived,
                simulation_params=simulation_params,
            )
        )

    return cases
