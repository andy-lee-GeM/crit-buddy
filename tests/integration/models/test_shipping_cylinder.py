import math
import unittest
from pathlib import Path

from critbuddy.core.template_loader import load_template_class


ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ROOT / "templates"


class ShippingCylinderTemplateTests(unittest.TestCase):
    def test_shipping_cylinder_derives_standard_volume_fields(self):
        template = load_template_class("shipping_cylinder", TEMPLATES)

        params = template.apply_defaults(
            {
                "enrichment": 20.0,
                "fissile_material": "uo2f2",
                "h_to_u": 5.0,
                "fill_fraction": 0.25,
                "cylinder_type": "48y",
            }
        )

        derived = template.derive_params(params)
        total_volume_cm3 = math.pi * derived["R_INNER"] ** 2 * derived["HEIGHT_CM"]

        self.assertAlmostEqual(derived["TOTAL_FUEL_VOLUME_CM3"], total_volume_cm3, places=6)
        self.assertAlmostEqual(derived["TOTAL_FUEL_VOLUME_L"], total_volume_cm3 / 1000.0, places=6)
        self.assertAlmostEqual(derived["FILL_VOLUME_CM3"], total_volume_cm3 * 0.25, places=6)
        self.assertAlmostEqual(derived["FILL_VOLUME_L"], total_volume_cm3 * 0.25 / 1000.0, places=6)


if __name__ == "__main__":
    unittest.main()
