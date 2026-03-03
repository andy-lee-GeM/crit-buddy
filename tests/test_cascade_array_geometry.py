import unittest
from pathlib import Path
import shutil

import openmc

from critbuddy.core.template_loader import load_template_class, load_template_module
from critbuddy.solvers.openmc.solver import OpenMCSolver


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class CascadeArrayGeometryTests(unittest.TestCase):
    def _base_params(self) -> dict:
        return {
            "enrichment": 20.0,
            "fissile_material": "uf6",
            "R_inner_cm": 12.7,
            "H_inner_cm": 101.5,
            "t_wall_cm": 0.3175,
            "wall_material": "steel",
            "i": 2,
            "j": 5,
            "k": 5,
            "gap_xy_cm": 6.0,
            "gap_z_cm": 100.0,
            "environment_material": "humid_air",
            "reflector_thickness_cm": 30.0,
        }

    def _derive(self, overrides: dict | None = None) -> dict:
        template = load_template_class("cascade_array")
        user = dict(self._base_params())
        if overrides:
            user.update(overrides)
        params = template.apply_defaults(user)
        errors = template.validate_params(params)
        self.assertEqual(errors, [], f"Validation errors: {errors}")
        return template.derive_params(params)

    def _build(self, overrides: dict | None = None):
        derived = self._derive(overrides=overrides)
        module = load_template_module(TEMPLATES / "cascade_array")
        openmc.reset_auto_ids()
        materials, geometry, dims = module.build_model(derived)
        return derived, materials, geometry, dims, module

    def _placements(self, overrides: dict | None = None):
        derived = self._derive(overrides=overrides)
        module = load_template_module(TEMPLATES / "cascade_array")
        return derived, list(module.iter_cylinder_placements(derived))

    def test_iter_cylinder_placements_known_counts(self):
        cases = [
            ({"i": 1, "j": 1, "k": 1}, 1),
            ({"i": 2, "j": 2, "k": 1}, 4),
            ({"i": 2, "j": 3, "k": 2}, 12),
        ]
        for overrides, expected_count in cases:
            _, placements = self._placements(overrides)
            self.assertEqual(len(placements), expected_count)

    def test_iter_cylinder_placements_order_layer_then_j_then_i(self):
        _, placements = self._placements(
            {
                "i": 2,
                "j": 2,
                "k": 2,
                "R_inner_cm": 10.0,
                "H_inner_cm": 20.0,
                "t_wall_cm": 1.0,
                "gap_xy_cm": 4.0,
                "gap_z_cm": 30.0,
            }
        )
        got = [(p.layer, p.j_idx, p.i_idx) for p in placements]
        expected = [
            (0, 0, 0),
            (0, 0, 1),
            (0, 1, 0),
            (0, 1, 1),
            (1, 0, 0),
            (1, 0, 1),
            (1, 1, 0),
            (1, 1, 1),
        ]
        self.assertEqual(got, expected)

    def test_physical_coordinates_single_cylinder(self):
        d, placements = self._placements(
            {
                "R_inner_cm": 10.0,
                "H_inner_cm": 20.0,
                "t_wall_cm": 1.0,
                "i": 1,
                "j": 1,
                "k": 1,
                "gap_xy_cm": 4.0,
                "gap_z_cm": 30.0,
            }
        )
        self.assertEqual(len(placements), 1)
        p0 = placements[0]

        self.assertAlmostEqual(d["R_OUTER"], 11.0, places=6)
        self.assertAlmostEqual(d["H_OUTER"], 22.0, places=6)
        self.assertAlmostEqual(p0.x_center, 11.0, places=6)
        self.assertAlmostEqual(p0.y_center, 11.0, places=6)
        self.assertAlmostEqual(p0.z_base, 0.0, places=6)

    def test_physical_coordinates_xy_spacing_and_gap(self):
        d, placements = self._placements(
            {
                "R_inner_cm": 10.0,
                "H_inner_cm": 20.0,
                "t_wall_cm": 1.0,
                "i": 2,
                "j": 2,
                "k": 1,
                "gap_xy_cm": 4.0,
                "gap_z_cm": 30.0,
            }
        )
        self.assertEqual(len(placements), 4)

        # With R_outer=11 and gap_xy=4, center pitch is 26 in both X and Y.
        # Generator order is layer -> j -> i.
        expected = [
            (11.0, 11.0, 0.0),
            (37.0, 11.0, 0.0),
            (11.0, 37.0, 0.0),
            (37.0, 37.0, 0.0),
        ]
        for actual, exp in zip(placements, expected):
            self.assertAlmostEqual(actual.x_center, exp[0], places=6)
            self.assertAlmostEqual(actual.y_center, exp[1], places=6)
            self.assertAlmostEqual(actual.z_base, exp[2], places=6)

        pitch_xy = placements[1].x_center - placements[0].x_center
        wall_to_wall_gap_xy = pitch_xy - 2.0 * d["R_OUTER"]
        self.assertAlmostEqual(pitch_xy, 26.0, places=6)
        self.assertAlmostEqual(wall_to_wall_gap_xy, 4.0, places=6)

    def test_physical_coordinates_z_spacing_and_gap(self):
        d, placements = self._placements(
            {
                "R_inner_cm": 10.0,
                "H_inner_cm": 20.0,
                "t_wall_cm": 1.0,
                "i": 1,
                "j": 1,
                "k": 2,
                "gap_xy_cm": 4.0,
                "gap_z_cm": 30.0,
            }
        )
        self.assertEqual(len(placements), 2)

        # With H_outer=22 and gap_z=30, Z pitch is 52 between layer bases.
        expected = [
            (11.0, 11.0, 0.0),
            (11.0, 11.0, 52.0),
        ]
        for actual, exp in zip(placements, expected):
            self.assertAlmostEqual(actual.x_center, exp[0], places=6)
            self.assertAlmostEqual(actual.y_center, exp[1], places=6)
            self.assertAlmostEqual(actual.z_base, exp[2], places=6)

        pitch_z = placements[1].z_base - placements[0].z_base
        cap_to_cap_gap_z = pitch_z - d["H_OUTER"]
        self.assertAlmostEqual(pitch_z, 52.0, places=6)
        self.assertAlmostEqual(cap_to_cap_gap_z, 30.0, places=6)

    def test_visualization_plot_generation_staged_cases(self):
        if shutil.which("openmc") is None:
            self.skipTest("openmc executable not on PATH")

        template = load_template_class("cascade_array")
        solver = OpenMCSolver()
        template_dir = TEMPLATES / "cascade_array"
        output_root = Path(__file__).resolve().parent / "_visualizations" / "cascade_array"
        output_root.mkdir(parents=True, exist_ok=True)

        staged_cases = [
            ("01_single_i1_j1_k1", {"i": 1, "j": 1, "k": 1}),
            ("02_xy_i2_j5_k1", {"i": 2, "j": 5, "k": 1}),
            ("03_z_i1_j1_k5", {"i": 1, "j": 1, "k": 5}),
            ("04_full_i2_j5_k5", {"i": 2, "j": 5, "k": 5}),
        ]

        for case_name, overrides in staged_cases:
            user = self._base_params()
            user.update({"boundary_type": "vacuum"})
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
            self.assertGreater(
                image_file.stat().st_size,
                0,
                f"Empty geometry image for {case_name}",
            )


if __name__ == "__main__":
    unittest.main()
