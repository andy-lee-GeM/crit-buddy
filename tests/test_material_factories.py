import unittest

from critbuddy.core.materials import (
    create_environment_material,
    create_fissile_material,
)


class MaterialFactoryTests(unittest.TestCase):
    def test_create_fissile_material_uf6_defaults(self):
        mat = create_fissile_material("uf6", enrichment_pct=5.0)
        self.assertEqual(mat.name, "UF6")
        self.assertAlmostEqual(mat.density, 5.09, places=3)

    def test_create_fissile_material_uo2f2_uses_h_to_u(self):
        mat = create_fissile_material(
            "uo2f2",
            enrichment_pct=5.0,
            h_to_u=30.0,
        )
        self.assertTrue(mat.name.startswith("UO2F2"))
        nuclides = {n.name for n in mat.nuclides}
        self.assertIn("O16", nuclides)
        self.assertIn("H1", nuclides)

    def test_create_environment_material_density_override(self):
        mat = create_environment_material(
            "humid_air",
            environment_density=0.0015,
        )
        self.assertEqual(mat.name, "Humid_Air")
        self.assertAlmostEqual(mat.density, 0.0015, places=6)


if __name__ == "__main__":
    unittest.main()
