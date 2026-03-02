import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from critbuddy.analysis.orchestrator import run_analysis_workflow


class AnalysisWorkflowIntegrationTests(unittest.TestCase):
    def test_experiment_runs_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            experiment_dir = Path(tmp)
            config_dir = experiment_dir / "_config"
            config_dir.mkdir(parents=True, exist_ok=True)

            for name in (
                "01_uf6_dry.yaml",
                "02_hu_opt.yaml",
                "03_wet_bottom_fill.yaml",
            ):
                (config_dir / name).write_text("name: test\n")

            def fake_subprocess_run(cmd, cwd):
                # cmd: [python, run_study.py, <config>, --solver, <solver>]
                config_path = Path(cmd[2])
                step_id = config_path.stem
                (experiment_dir / "runs" / step_id / "2026-03-02_00-00-00").mkdir(parents=True, exist_ok=True)
                return SimpleNamespace(returncode=0)

            with patch("critbuddy.analysis.orchestrator.subprocess.run", side_effect=fake_subprocess_run):
                result = run_analysis_workflow(experiment_dir)

            self.assertTrue(result.success)
            self.assertIsNone(result.error)
            self.assertEqual(
                result.completed_steps,
                ["01_uf6_dry", "02_hu_opt", "03_wet_bottom_fill"],
            )


if __name__ == "__main__":
    unittest.main()
