import shutil
import unittest
from pathlib import Path

from critbuddy.core.template_loader import load_template_class
from critbuddy.solvers.openmc.solver import OpenMCSolver


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class CascadeArrayModelTests(unittest.TestCase):
    def _base_params(self) -> dict:
        # Intentionally whole-number geometry for easy mental math.
        return {
            "enrichment": 5.0,
            "fissile_material": "uf6",
            "R_inner_cm": 10.0,
            "H_inner_cm": 20.0,
            "t_wall_cm": 1.0,
            "wall_material": "steel",
            "i": 2,
            "j": 2,
            "k": 2,
            "gap_xy_cm": 4.0,
            "gap_z_cm": 6.0,
            "environment_material": "air",
            "reflector_thickness_cm": 10.0,
        }

    def test_visualization_plot_generation_staged_cases(self):
        if shutil.which("openmc") is None:
            self.skipTest("openmc executable not on PATH")

        template = load_template_class("cascade_array")
        solver = OpenMCSolver(show_progress=False)
        template_dir = TEMPLATES / "cascade_array"
        output_root = Path(__file__).resolve().parent / "_visualizations" / "cascade_array_model"
        output_root.mkdir(parents=True, exist_ok=True)

        staged_cases = [
            ("01_single_cylinder", {"i": 1, "j": 1, "k": 1}),
            ("02_single_cassette_4x1", {"i": 4, "j": 1, "k": 1}),
            ("03_single_cassette_2x3", {"i": 2, "j": 3, "k": 1}),
            ("04_cassette_stack_2x2_2", {"i": 2, "j": 2, "k": 2}),
            ("05_cassette_stack_4x3_2", {"i": 4, "j": 3, "k": 5}),
            ("06_cassette_stack_5x2_2", {"i": 5, "j": 2, "k": 5}),
        ]

        for case_name, overrides in staged_cases:
            user = self._base_params()
            user.update(overrides)

            params = template.apply_defaults(user)
            errors = template.validate_params(params)
            self.assertEqual(errors, [], f"Validation errors for {case_name}: {errors}")
            derived = template.derive_params(params)

            case_dir = output_root / case_name
            image_path = solver.validate(
                derived,
                case_dir=case_dir,
                template_dir=template_dir,
            )

            self.assertIsNotNone(image_path, f"No geometry image produced for {case_name}")
            image_file = Path(image_path)
            self.assertTrue(image_file.exists(), f"Missing geometry image for {case_name}")
            self.assertGreater(image_file.stat().st_size, 0, f"Empty geometry image for {case_name}")

    def test_visualization_plot_generation_fill_fraction_staged_cases(self):
        if shutil.which("openmc") is None:
            self.skipTest("openmc executable not on PATH")

        template = load_template_class("cascade_array")
        solver = OpenMCSolver(show_progress=False)
        template_dir = TEMPLATES / "cascade_array"
        output_root = Path(__file__).resolve().parent / "_visualizations" / "cascade_array_model_fill"
        output_root.mkdir(parents=True, exist_ok=True)

        staged_cases = [
            ("01_fill_25pct", {"fill_fraction": 0.25}),
            ("02_fill_50pct", {"fill_fraction": 0.50}),
            ("03_fill_75pct", {"fill_fraction": 0.75}),
        ]

        for case_name, overrides in staged_cases:
            user = self._base_params()
            user.update(overrides)

            params = template.apply_defaults(user)
            errors = template.validate_params(params)
            self.assertEqual(errors, [], f"Validation errors for {case_name}: {errors}")
            derived = template.derive_params(params)

            case_dir = output_root / case_name
            image_path = solver.validate(
                derived,
                case_dir=case_dir,
                template_dir=template_dir,
            )

            self.assertIsNotNone(image_path, f"No geometry image produced for {case_name}")
            image_file = Path(image_path)
            self.assertTrue(image_file.exists(), f"Missing geometry image for {case_name}")
            self.assertGreater(image_file.stat().st_size, 0, f"Empty geometry image for {case_name}")


if __name__ == "__main__":
    unittest.main()
