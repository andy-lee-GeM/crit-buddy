"""
Base solver abstraction for Monte Carlo criticality calculations.

Defines the interface that all solver backends must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from critbuddy.utils import Status


@dataclass
class SolverResult:
    """Result from a solver execution."""

    keff: float
    uncertainty: float
    status: Status
    solver_name: str
    case_label: str
    execution_time: float
    output_files: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def k2sigma(self) -> float:
        """k-eff + 2 standard deviations (conservative estimate)."""
        return self.keff + 2 * self.uncertainty

    @classmethod
    def failed(cls, solver_name: str, case_label: str, error_msg: str) -> "SolverResult":
        """Create a failed result."""
        return cls(
            keff=0.0,
            uncertainty=0.0,
            status=Status.FAILED,
            solver_name=solver_name,
            case_label=case_label,
            execution_time=0.0,
            errors=[error_msg],
        )

    @classmethod
    def skipped(cls, solver_name: str, case_label: str, reason: str) -> "SolverResult":
        """Create a skipped result."""
        return cls(
            keff=0.0,
            uncertainty=0.0,
            status=Status.SKIPPED,
            solver_name=solver_name,
            case_label=case_label,
            execution_time=0.0,
            warnings=[reason],
        )


def compute_status(keff: float, uncertainty: float, safety_limit: float = 0.95) -> Status:
    """
    Compute safety status based on k-eff and uncertainty.

    Classification:
        SAFE: k_eff + 2*sigma < safety_limit
        MARGINAL: k_eff + 2*sigma >= safety_limit but < 1.0
        CRITICAL: k_eff + 2*sigma >= 1.0

    Args:
        keff: Calculated k-effective value
        uncertainty: Standard deviation of k-eff
        safety_limit: Upper limit for k-eff (default 0.95)

    Returns:
        Status enum value
    """
    k2s = keff + 2 * uncertainty
    if k2s < safety_limit:
        return Status.SAFE
    elif k2s < 1.0:
        return Status.MARGINAL
    else:
        return Status.CRITICAL


class Solver(ABC):
    """Abstract base class for Monte Carlo solvers."""

    name: str = "base"

    @abstractmethod
    def run(
        self,
        params: dict,
        case_label: str,
        case_dir: Path,
        template_dir: Path,
        safety_limit: float = 0.95,
    ) -> SolverResult:
        """
        Execute a simulation and return results.

        Args:
            params: Dictionary of parameters for the model
            case_label: Label for this case (e.g., "2-inch")
            case_dir: Directory to run the case in
            template_dir: Directory containing template files
            safety_limit: Upper limit for safety classification

        Returns:
            SolverResult with k-eff and status
        """
        pass

    @abstractmethod
    def validate(
        self,
        params: dict,
        case_dir: Path,
        template_dir: Path,
    ) -> Optional[Path]:
        """
        Generate visualization/validation output.

        Args:
            params: Dictionary of parameters for the model
            case_dir: Directory for validation output
            template_dir: Directory containing template files

        Returns:
            Path to validation image, or None if not supported
        """
        pass

    def is_available(self) -> bool:
        """Check if this solver is available (executable found, etc.)."""
        return True
