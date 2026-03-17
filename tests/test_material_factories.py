import unittest

from critbuddy.core.materials import (
    create_environment_material,
    create_fissile_material,
    get_material,
    uo2f2,
    void,
)


class MaterialFactoryTests(unittest.TestCase):
    def test_uo2f2_constructor_uses_enrichment_and_density(self):
        mat = uo2f2(enrichment_pct=5.0, density=6.10)

        self.assertEqual(mat.name, "UO2F2")
        self.assertAlmostEqual(mat.density, 6.10, places=6)
        nuclides = {n.name for n in mat.nuclides}
        self.assertEqual(nuclides, {"U235", "U238", "H1", "O16", "F19"})

    def test_create_fissile_material_uf6_defaults(self):
        mat = create_fissile_material("uf6", enrichment_pct=5.0)
        self.assertEqual(mat.name, "UF6")
        self.assertAlmostEqual(mat.density, 5.09, places=3)

    def test_create_fissile_material_uo2f2_uses_density(self):
        mat = create_fissile_material(
            "uo2f2",
            enrichment_pct=5.0,
            fissile_density=6.20,
        )
        self.assertEqual(mat.name, "UO2F2")
        self.assertAlmostEqual(mat.density, 6.20, places=6)
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

    def test_void_material_uses_cross_section_safe_isotopes(self):
        mat = void()
        nuclides = {n.name for n in mat.nuclides}

        self.assertEqual(nuclides, {"N14", "O16", "Ar40"})

    def test_create_fissile_material_uo2f2_defaults_density(self):
        mat = create_fissile_material("uo2f2", enrichment_pct=5.0)
        self.assertAlmostEqual(mat.density, 4.4, places=6)

    def test_ss304_material_uses_library_defaults(self):
        mat = get_material("ss304")

        self.assertEqual(mat.name, "Stainless_Steel_304")
        self.assertAlmostEqual(mat.density, 7.93, places=6)
        nuclides = {n.name for n in mat.nuclides}
        self.assertIn("Fe56", nuclides)
        self.assertIn("Cr52", nuclides)
        self.assertIn("Ni58", nuclides)
        self.assertIn("Mn55", nuclides)

    def test_humid_air_material_uses_library_defaults(self):
        mat = create_environment_material("humid_air")
        nuclides = {n.name: n.percent for n in mat.nuclides}

        self.assertEqual(mat.name, "Humid_Air")
        self.assertAlmostEqual(mat.density, 0.0011, places=8)
        self.assertEqual(
            nuclides,
            {
                "N14": 0.702,
                "O16": 0.223,
                "Ar40": 0.004,
                "H1": 0.071,
            },
        )


if __name__ == "__main__":
    unittest.main()
