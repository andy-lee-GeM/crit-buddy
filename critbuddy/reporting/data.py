"""
Data loading and analysis for results reporting.

Handles loading results CSV and detecting swept parameters.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


# Standard columns in results CSV (not parameters)
STANDARD_COLUMNS = {"case", "solver", "keff", "std", "keff_2sigma", "status", "execution_time"}


@dataclass
class StudyResults:
    """Loaded and analyzed study results."""

    data: pd.DataFrame
    swept_params: List[str]
    fixed_params: Dict[str, Any]
    solvers: List[str]

    @classmethod
    def from_csv(cls, csv_path: Path) -> "StudyResults":
        """Load results from CSV file."""
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"Results file not found: {csv_path}")

        df = pd.read_csv(csv_path)

        # Identify parameter columns (everything not in standard columns)
        param_cols = [c for c in df.columns if c not in STANDARD_COLUMNS]

        # Detect swept vs fixed parameters
        swept = []
        fixed = {}

        for col in param_cols:
            unique_values = df[col].dropna().unique()
            if len(unique_values) > 1:
                swept.append(col)
            elif len(unique_values) == 1:
                fixed[col] = unique_values[0]

        solvers = df["solver"].unique().tolist()

        return cls(
            data=df,
            swept_params=swept,
            fixed_params=fixed,
            solvers=solvers,
        )

    @property
    def has_multiple_solvers(self) -> bool:
        """Check if results include multiple solvers."""
        return len(self.solvers) > 1

    @property
    def n_cases(self) -> int:
        """Number of unique cases."""
        return self.data["case"].nunique()

    def get_solver_data(self, solver: str) -> pd.DataFrame:
        """Get data for a specific solver."""
        return self.data[self.data["solver"] == solver].copy()

    def get_comparison_data(self) -> pd.DataFrame:
        """
        Get data pivoted for solver comparison.

        Returns DataFrame with one row per case, columns for each solver's k-eff.
        """
        if not self.has_multiple_solvers:
            raise ValueError("Comparison requires multiple solvers")

        # Pivot k-eff values
        keff_pivot = self.data.pivot(index="case", columns="solver", values="keff")
        std_pivot = self.data.pivot(index="case", columns="solver", values="std")

        # Get parameter values (same for all solvers, just take first)
        param_data = self.data.groupby("case")[self.swept_params].first()

        # Combine
        result = param_data.copy()
        for solver in self.solvers:
            result[f"{solver}_keff"] = keff_pivot[solver]
            result[f"{solver}_std"] = std_pivot[solver]

        # Calculate delta if we have openmc and mcnp
        if "openmc" in self.solvers and "mcnp" in self.solvers:
            result["delta_keff"] = result["openmc_keff"] - result["mcnp_keff"]
            result["delta_pcm"] = result["delta_keff"] * 1e5

        return result.reset_index()

    def summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the study."""
        df = self.data

        stats = {
            "n_cases": self.n_cases,
            "n_solvers": len(self.solvers),
            "solvers": self.solvers,
            "swept_params": self.swept_params,
            "fixed_params": self.fixed_params,
        }

        # Per-solver stats
        for solver in self.solvers:
            solver_df = df[df["solver"] == solver]
            stats[f"{solver}_max_keff"] = solver_df["keff"].max()
            stats[f"{solver}_max_k2s"] = solver_df["keff_2sigma"].max()

            # Status counts
            status_counts = solver_df["status"].value_counts().to_dict()
            stats[f"{solver}_status"] = status_counts

        return stats
