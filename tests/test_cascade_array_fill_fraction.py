import unittest

from critbuddy.core.config import ExperimentConfig, generate_cases
from critbuddy.core.template_loader import load_template_class


class CascadeArrayFillFractionTests(unittest.TestCase):
    def setUp(self):
        self.template = load_template_class("cascade_array")

    def _base_params(self) -> dict:
        return {
            "enrichment": 20.0,
            "fissile_material": "uo2f2",
            "R_inner_cm": 12.7,
            "H_inner_cm": 101.5,
            "t_wall_cm": 0.3175,
            "wall_material": "steel",
            "i": 2,
            "j": 5,
            "k": 5,
            "gap_xy_cm": 1.0,
            "gap_z_cm": 100.0,
            "environment_material": "humid_air",
            "reflector_thickness_cm": 30.0,
            "h_to_u": 50.0,
        }

    def test_validate_accepts_fill_fraction_and_void_material(self):
        params = self._base_params()
        params["fill_fraction"] = 0.25
        params["void_material"] = "void"

        errors = self.template.validate_params(params)
        self.assertEqual(errors, [])

    def test_derive_params_computes_fissile_height(self):
        params = self._base_params()
        params["fill_fraction"] = 0.25

        derived = self.template.derive_params(self.template.apply_defaults(params))
        self.assertAlmostEqual(derived["FILL_FRACTION"], 0.25, places=6)
        self.assertAlmostEqual(derived["FISSILE_HEIGHT"], 101.5 * 0.25, places=6)
        self.assertEqual(derived["VOID_MATERIAL"], "void")

    def test_generate_cases_expands_fill_fraction_sweep(self):
        config_dict = {
            "problem": "cascade_array",
            "name": "fill sweep test",
            **self._base_params(),
            "fill_fraction": [0.25, 1.0],
        }
        cfg = ExperimentConfig.from_dict(config_dict)
        cases = generate_cases(cfg, self.template)

        self.assertEqual(len(cases), 2)
        ff_values = sorted(case.user_params["fill_fraction"] for case in cases)
        self.assertEqual(ff_values, [0.25, 1.0])


if __name__ == "__main__":
    unittest.main()
