import unittest
from pathlib import Path

import openmc

from critbuddy.runner import load_template_class, load_template_module


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class TemplateRefactorRegressionTests(unittest.TestCase):
    def _build(self, template_name: str, user_params: dict):
        template = load_template_class(template_name)
        params = template.apply_defaults(user_params)
        errors = template.validate_params(params)
        self.assertEqual(errors, [], f"Validation errors for {template_name}: {errors}")
        derived = template.derive_params(params)

        module = load_template_module(TEMPLATES / template_name)
        openmc.reset_auto_ids()
        materials, geometry, dims = module.build_model(derived)
        return derived, materials, geometry, dims

    def test_shipping_template_has_fissile_z_keys(self):
        template = load_template_class("shipping_cylinder")
        params = template.apply_defaults(
            {
                "enrichment": 5.0,
                "cylinder_type": "30b",
            }
        )
        errors = template.validate_params(params)
        self.assertEqual(errors, [])
        derived = template.derive_params(params)

        self.assertIn("Z_FISSILE_BOTTOM", derived)
        self.assertIn("Z_FISSILE_TOP", derived)

    def test_shipping_uo2f2_is_respected(self):
        _, materials, _, _ = self._build(
            "shipping_cylinder",
            {
                "enrichment": 5.0,
                "cylinder_type": "30b",
                "fissile_material": "uo2f2",
                "h_to_u": 20.0,
            },
        )
        names = {m.name for m in materials}
        self.assertTrue(any(name.startswith("UO2F2") for name in names))
        self.assertNotIn("UF6", names)

    def test_rectangular_box_uo2f2_is_respected(self):
        _, materials, _, _ = self._build(
            "rectangular_box",
            {
                "enrichment": 5.0,
                "fissile_material": "uo2f2",
                "h_to_u": 25.0,
                "length_cm": 20.0,
                "width_cm": 20.0,
                "height_cm": 20.0,
            },
        )
        names = {m.name for m in materials}
        self.assertTrue(any(name.startswith("UO2F2") for name in names))
        self.assertNotIn("UF6", names)

    def test_environment_material_and_density_propagate(self):
        derived, _, _, _ = self._build(
            "cylinder",
            {
                "enrichment": 5.0,
                "radius_cm": 5.0,
                "height_cm": 20.0,
                "environment_material": "air",
                "environment_density": 0.0014,
            },
        )
        self.assertEqual(derived["ENVIRONMENT_MATERIAL"], "air")
        self.assertAlmostEqual(derived["ENV_DENSITY"], 0.0014, places=6)

    def test_legacy_environment_alias_is_rejected(self):
        template = load_template_class("pipe")
        params = template.apply_defaults(
            {
                "enrichment": 5.0,
                "pipe_size": "2",
                "length_cm": 100.0,
                "environment": "water",
            }
        )
        errors = template.validate_params(params)
        self.assertTrue(any("Unknown parameter 'environment'" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
