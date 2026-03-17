#!/usr/bin/env python3
"""
Analysis workflow orchestration.

Minimal workflow:
1. 01_uf6_dry.yaml
2. 02_hu_opt.yaml
3. 03_wet_bottom_fill.yaml
4. 04_wet_torus_fill.yaml (optional)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CRIT_BUDDY_ROOT = Path(__file__).resolve().parents[2]
RUN_STUDY = CRIT_BUDDY_ROOT / "run_study.py"
PYTHON_EXE = sys.executable


@dataclass
class AnalysisResult:
    """Result for a full analysis workflow run."""

    experiment_dir: Path
    completed_steps: list[str]
    success: bool
    error: str | None = None


def _run_config(config_path: Path, solver: str) -> None:
    cmd = [PYTHON_EXE, str(RUN_STUDY), str(config_path), "--solver", solver]
    return_code = subprocess.run(cmd, cwd=str(CRIT_BUDDY_ROOT)).returncode
    if return_code != 0:
        raise RuntimeError(f"run_study failed with return code {return_code} for {config_path.name}")


def _print_manual_handoff(config_name: str) -> None:
    if config_name == "01_uf6_dry.yaml":
        print("\nManual checkpoint: update 02_hu_opt.yaml with worst-case geometry from step 1 results.")
    elif config_name == "02_hu_opt.yaml":
        print("\nManual checkpoint: update wet configs with peak H/U from step 2 results.")


def run_step(config_path: Path, solver: str = "openmc") -> str:
    """Run one config file and return its step id."""
    config_path = Path(config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    print(f"\n{'=' * 60}")
    print(f"Running: {config_path.name}")
    print(f"{'=' * 60}")
    _run_config(config_path, solver=solver)
    return config_path.stem


def run_analysis_workflow(
    experiment_dir: Path,
    solver: str = "openmc",
) -> AnalysisResult:
    """Run the standard 3(+1 optional) analysis workflow."""
    experiment_dir = Path(experiment_dir).resolve()
    config_dir = experiment_dir / "_config"

    workflow_configs = [
        config_dir / "01_uf6_dry.yaml",
        config_dir / "02_hu_opt.yaml",
        config_dir / "03_wet_bottom_fill.yaml",
        config_dir / "04_wet_torus_fill.yaml",
    ]

    completed_steps: list[str] = []

    for config_path in workflow_configs:
        if not config_path.exists():
            if config_path.name == "04_wet_torus_fill.yaml":
                print(f"\nSkipping optional step (missing config: {config_path.name})")
                continue
            return AnalysisResult(
                experiment_dir=experiment_dir,
                completed_steps=completed_steps,
                success=False,
                error=f"Missing required config: {config_path}",
            )

        try:
            step_id = run_step(config_path, solver=solver)
        except Exception as exc:
            return AnalysisResult(
                experiment_dir=experiment_dir,
                completed_steps=completed_steps,
                success=False,
                error=str(exc),
            )

        completed_steps.append(step_id)
        _print_manual_handoff(config_path.name)

    return AnalysisResult(
        experiment_dir=experiment_dir,
        completed_steps=completed_steps,
        success=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run crit-buddy analysis workflow")
    parser.add_argument("experiment_dir", help="Path to experiment directory")
    parser.add_argument("--solver", choices=["openmc"], default="openmc")
    args = parser.parse_args()

    result = run_analysis_workflow(
        experiment_dir=Path(args.experiment_dir),
        solver=args.solver,
    )

    print("\n" + "=" * 60)
    print("WORKFLOW SUMMARY")
    print("=" * 60)
    if result.completed_steps:
        print("Completed steps:")
        for step_id in result.completed_steps:
            print(f"- {step_id}")
    else:
        print("No steps completed.")

    if result.error:
        print(f"\nError: {result.error}")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
