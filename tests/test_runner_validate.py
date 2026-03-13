import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from critbuddy.core.config import Case
from critbuddy.runner import validate_geometry


class RunnerValidateTests(unittest.TestCase):
    def test_validate_geometry_uses_first_generated_case(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            experiment_dir = root / "experiment"
            config_dir = experiment_dir / "_config"
            config_dir.mkdir(parents=True)
            config_path = config_dir / "demo.yaml"
            config_path.write_text("problem: cascade_array\nname: demo\n", encoding="ascii")

            first_case = Case(
                label="case_1",
                user_params={"fill_fraction": 0.1},
                derived_params={"DERIVED": 1},
            )
            second_case = Case(
                label="case_2",
                user_params={"fill_fraction": 0.2},
                derived_params={"DERIVED": 2},
            )

            solver = Mock()
            expected_image = experiment_dir / "_validation" / "geometry.png"
            solver.validate.return_value = expected_image

            with patch("critbuddy.runner.load_template_class", return_value=object()), patch(
                "critbuddy.runner.generate_cases",
                return_value=[first_case, second_case],
            ), patch("critbuddy.runner.create_solvers", return_value=[solver]):
                image_path = validate_geometry(config_path, solver="openmc")

            self.assertEqual(image_path, expected_image)
            solver.validate.assert_called_once()

            _, kwargs = solver.validate.call_args
            self.assertEqual(kwargs["params"], first_case.all_params)
            self.assertEqual(kwargs["case_dir"], experiment_dir / "_validation")


if __name__ == "__main__":
    unittest.main()
