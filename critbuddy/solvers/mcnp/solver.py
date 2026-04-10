"""
MCNP solver backend for criticality calculations.
"""

import importlib.util
import os
import time
from pathlib import Path
from typing import Optional

from critbuddy.solvers.base import Solver, SolverResult, compute_status
from critbuddy.solvers.mcnp.executor import MCNPExecutor
from critbuddy.solvers.mcnp.parser import MCNPOutputParser
from critbuddy.solvers.mcnp import template
from critbuddy.utils import get_logger

logger = get_logger(__name__)


class MCNPSolver(Solver):
    """MCNP Monte Carlo solver."""

    name = "mcnp"

    def __init__(
        self,
        executable: str = None,
        tasks: int = 4,
        timeout: int = 3600,
    ):
        """
        Initialize MCNP solver.

        Args:
            executable: Path to MCNP executable
            tasks: Number of parallel tasks
            timeout: Execution timeout in seconds
        """
        self.executable = executable
        self.tasks = tasks
        self.timeout = timeout
        self.executor = MCNPExecutor(executable, tasks, timeout)
        self.parser = MCNPOutputParser()

    def _find_template(self, template_dir: Path) -> Optional[Path]:
        """Find MCNP template file in template directory."""
        mcnp_dir = template_dir / "mcnp"
        if mcnp_dir.exists():
            for name in ["template.inp", "template.i"]:
                path = mcnp_dir / name
                if path.exists():
                    return path
        return None

    def _load_model(self, template_dir: Path):
        """Load MCNP model.py if it exists."""
        model_path = template_dir / "mcnp" / "model.py"
        if not model_path.exists():
            return None

        spec = importlib.util.spec_from_file_location("mcnp_model", model_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run(
        self,
        params: dict,
        case_label: str,
        case_dir: Path,
        template_dir: Path,
        safety_limit: float = 0.95,
    ) -> SolverResult:
        """
        Run MCNP simulation.

        Args:
            params: Dictionary of parameters for the model
            case_label: Label for this case
            case_dir: Directory to run the case in
            template_dir: Directory containing template files
            safety_limit: Upper limit for safety classification

        Returns:
            SolverResult with k-eff and status
        """
        start_time = time.time()
        logger.debug(f"Starting MCNP run for case '{case_label}'")

        if not self.is_available():
            logger.warning(f"MCNP executable not found: {self.executable}")
            return SolverResult.skipped(
                solver_name=self.name,
                case_label=case_label,
                reason=f"MCNP executable not found: {self.executable}",
            )

        try:
            # Find template
            template_path = self._find_template(template_dir)
            if template_path is None:
                logger.error(f"No MCNP template found in {template_dir}")
                return SolverResult.failed(
                    solver_name=self.name,
                    case_label=case_label,
                    error_msg=f"No MCNP template found in {template_dir}",
                )

            logger.debug(f"Using template: {template_path}")

            # Load model.py if it exists (for materials generation)
            model = self._load_model(template_dir)

            # Build render params
            render_params = {**params, "CASE_LABEL": case_label}

            # Let model.py inject MCNP-specific render parameters.
            if model and hasattr(model, "build_render_params"):
                extra_params = model.build_render_params(params)
                if not isinstance(extra_params, dict):
                    raise TypeError("mcnp/model.py build_render_params() must return a dict")
                render_params.update(extra_params)
            elif model and hasattr(model, "build_materials"):
                materials = model.build_materials(params)
                if isinstance(materials, dict):
                    render_params.update(materials)
                else:
                    render_params["MATERIALS"] = materials

            # Create case directory and render template
            case_dir = Path(case_dir)
            case_dir.mkdir(parents=True, exist_ok=True)
            input_file = case_dir / "input"
            template.render_file(template_path, render_params, input_file)

            # Run MCNP
            exec_result = self.executor.run(
                input_file=Path("input"),
                working_dir=case_dir,
            )

            if not exec_result.success:
                return SolverResult.failed(
                    solver_name=self.name,
                    case_label=case_label,
                    error_msg=exec_result.error_message or "MCNP execution failed",
                )

            # Parse output
            output_file = case_dir / "inputo"
            parsed = self.parser.parse(output_file)

            if not parsed.success:
                return SolverResult.failed(
                    solver_name=self.name,
                    case_label=case_label,
                    error_msg="Failed to parse k-eff from MCNP output",
                )

            execution_time = time.time() - start_time
            status = compute_status(parsed.keff, parsed.uncertainty, safety_limit)

            return SolverResult(
                keff=parsed.keff,
                uncertainty=parsed.uncertainty,
                status=status,
                solver_name=self.name,
                case_label=case_label,
                execution_time=execution_time,
                output_files=[input_file, output_file],
                warnings=parsed.warnings,
                errors=parsed.fatal_errors,
            )

        except Exception as e:
            return SolverResult.failed(
                solver_name=self.name,
                case_label=case_label,
                error_msg=str(e),
            )

    def validate(
        self,
        params: dict,
        case_dir: Path,
        template_dir: Path,
    ) -> Optional[Path]:
        """MCNP geometry validation not implemented."""
        return None

    def is_available(self) -> bool:
        """Check if MCNP executable exists."""
        return self.executor.is_available()
