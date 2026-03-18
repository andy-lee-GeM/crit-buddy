import unittest

from critbuddy.core.geometry.cylinders import (
    CYLINDER_REGISTRY,
    cylinder_info,
    get_cylinder,
    get_inner_diameter,
    get_inner_radius,
    get_internal_volume,
    list_cylinders,
)


class CylinderRegistryTests(unittest.TestCase):
    def test_get_cylinder_returns_registry_spec(self):
        spec = get_cylinder("30b")

        self.assertEqual(spec.name, "30B Cylinder")
        self.assertEqual(spec.wall_material, "steel")
        self.assertIs(spec, CYLINDER_REGISTRY["30b"])

    def test_inner_geometry_helpers_match_registry_values(self):
        self.assertAlmostEqual(get_inner_radius("30b"), 37.30625, places=6)
        self.assertAlmostEqual(get_inner_diameter("30b"), 74.6125, places=6)
        self.assertAlmostEqual(get_internal_volume("30b"), 743.296327, places=3)

    def test_list_cylinders_includes_common_sizes(self):
        names = list_cylinders()
        self.assertIn("30b", names)
        self.assertIn("48y", names)

    def test_cylinder_info_contains_key_fields(self):
        info = cylinder_info("30b")
        self.assertIn("30B Cylinder", info)
        self.assertIn("Wall material: steel", info)

    def test_unknown_cylinder_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_cylinder("missing")


if __name__ == "__main__":
    unittest.main()
