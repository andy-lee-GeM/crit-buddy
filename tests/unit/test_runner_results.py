import csv
import tempfile
import unittest
from pathlib import Path

from critbuddy.runner import _build_display_params, write_results
from critbuddy.utils import Status


class RunnerResultsTests(unittest.TestCase):
    def test_build_display_params_overlays_resolved_user_values(self):
        display = _build_display_params(
            user_params={
                "fill_height_cm": 20.0,
                "fill_fraction_percent": 3.0,
                "inner_radius_cm": 59.3725,
            },
            derived_params={
                "FILL_HEIGHT_CM": 9.0678,
                "FILL_FRACTION_PERCENT": 3.0,
                "INNER_RADIUS_CM": 59.3725,
                "TOTAL_X_CM": 709.6,
            },
        )

        self.assertAlmostEqual(display["fill_height_cm"], 9.0678, places=4)
        self.assertAlmostEqual(display["fill_fraction_percent"], 3.0, places=6)
        self.assertAlmostEqual(display["inner_radius_cm"], 59.3725, places=6)
        self.assertNotIn("total_x_cm", display)

    def test_write_results_uses_display_params(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            results_path = write_results(
                run_dir,
                {
                    "openmc": [
                        {
                            "case": "case_1",
                            "solver": "openmc",
                            "keff": 0.71707,
                            "std": 0.00110,
                            "k2s": 0.71927,
                            "status": Status.SAFE,
                            "execution_time": 31.2,
                            "user_params": {
                                "fill_height_cm": 20.0,
                                "fill_fraction_percent": 3.0,
                            },
                            "display_params": {
                                "fill_height_cm": 9.0678,
                                "fill_fraction_percent": 3.0,
                            },
                        }
                    ]
                },
            )

            self.assertIsNotNone(results_path)
            with open(results_path, newline="") as f:
                rows = list(csv.DictReader(f))

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["fill_fraction_percent"], "3.0")
            self.assertEqual(rows[0]["fill_height_cm"], "9.0678")


if __name__ == "__main__":
    unittest.main()
