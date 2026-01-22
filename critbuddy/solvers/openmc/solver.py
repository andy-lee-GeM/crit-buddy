"""
OpenMC solver backend for criticality calculations.
"""

import importlib.util
import time
from pathlib import Path
from typing import Optional

import openmc

from critbuddy.solvers.base import Solver, SolverResult, compute_status
from critbuddy.utils import working_directory, get_logger

logger = get_logger(__name__)


class OpenMCSolver(Solver):
    """OpenMC Monte Carlo solver."""

    name = "openmc"

    def __init__(self):
        """Initialize OpenMC solver."""
        pass

    def _load_template(self, template_dir: Path):
        """Dynamically load template module."""
        # Look in openmc subdirectory first (new structure)
        model_path = template_dir / "openmc" / "model.py"
        if not model_path.exists():
            # Fall back to old structure (model.py directly in template_dir)
            model_path = template_dir / "model.py"
        if not model_path.exists():
            raise FileNotFoundError(f"Template model not found: {model_path}")

        spec = importlib.util.spec_from_file_location("model", model_path)
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
        Run OpenMC simulation.

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
        logger.debug(f"Starting OpenMC run for case '{case_label}'")

        try:
            # Load template
            template = self._load_template(template_dir)
            logger.debug(f"Loaded template from {template_dir}")

            # Create case directory
            case_dir.mkdir(parents=True, exist_ok=True)

            with working_directory(case_dir):
                # Build model
                logger.debug("Building model...")
                materials, geometry, dims = template.build_model(params)

                # Export XML files
                materials.export_to_xml()
                geometry.export_to_xml()

                # Settings
                settings = template.create_settings(params, dims)
                settings.export_to_xml()

                # Run OpenMC
                openmc.run(output=False)

                # Extract results (handle both uppercase and lowercase param names)
                batches = params.get('BATCHES', params.get('batches', 150))
                statepoint_file = f"statepoint.{int(batches)}.h5"
                with openmc.StatePoint(statepoint_file) as sp:
                    keff = sp.keff.nominal_value
                    uncertainty = sp.keff.std_dev

            execution_time = time.time() - start_time
            status = compute_status(keff, uncertainty, safety_limit)

            return SolverResult(
                keff=keff,
                uncertainty=uncertainty,
                status=status,
                solver_name=self.name,
                case_label=case_label,
                execution_time=execution_time,
                output_files=[
                    case_dir / "materials.xml",
                    case_dir / "geometry.xml",
                    case_dir / "settings.xml",
                    case_dir / statepoint_file,
                ],
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
        """
        Generate geometry visualization.

        Args:
            params: Dictionary of parameters for the model
            case_dir: Directory for validation output
            template_dir: Directory containing template files

        Returns:
            Path to validation image
        """
        from critbuddy.visualization import create_geometry_plot

        template = self._load_template(template_dir)

        # Create validation directory
        case_dir.mkdir(parents=True, exist_ok=True)

        with working_directory(case_dir):
            # Build model
            materials, geometry, dims = template.build_model(params)

            # Export
            materials.export_to_xml()
            geometry.export_to_xml()

            # Create plots
            plots, color_legend = template.create_plots(dims, materials)
            plots.export_to_xml()
            openmc.plot_geometry()

            # Rename raw OpenMC plots
            for i, name in enumerate(["xy", "xz"], 1):
                src = Path(f"plot_{i}.png")
                if src.exists():
                    src.rename(f"{name}.png")

        # Create combined geometry plot
        xy_plot = case_dir / "xy.png"
        xz_plot = case_dir / "xz.png"
        output_path = case_dir / "geometry.png"

        if xy_plot.exists() and xz_plot.exists():
            create_geometry_plot(
                xy_plot_path=xy_plot,
                xz_plot_path=xz_plot,
                output_path=output_path,
                color_legend=color_legend,
            )
            return output_path

        return None

    def is_available(self) -> bool:
        """Check if OpenMC is available."""
        try:
            import openmc
            return True
        except ImportError:
            return False
