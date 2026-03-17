import unittest

from critbuddy.core.materials import uo2f2, water
from critbuddy.core.materials.material_properties import summarize_openmc_material


class MaterialPropertyTests(unittest.TestCase):
    def test_water_summary_reproduces_canonical_mcnp_atom_densities(self):
        mat = water(density_g_cm3=1.0)

        summary = summarize_openmc_material(mat)
        rows = {row.nuclide: row for row in summary.nuclides}

        self.assertAlmostEqual(summary.density_g_cm3, 1.0, places=9)
        self.assertEqual(f"{rows['H1'].atom_density_bcm:.3f}", "0.067")
        self.assertEqual(f"{rows['O16'].atom_density_bcm:.3f}", "0.033")

    def test_uo2f2_summary_from_readable_inputs_tracks_canonical_fuel_card(self):
        mat = uo2f2(
            enrichment_pct=20.0,
            h_to_u=5.0,
            density=4.33,
        )

        summary = summarize_openmc_material(mat)
        rows = {row.nuclide: row for row in summary.nuclides}

        self.assertAlmostEqual(summary.density_g_cm3, 4.33, places=9)
        self.assertAlmostEqual(rows["U235"].atom_density_bcm, 0.001496, places=5)
        self.assertAlmostEqual(rows["U238"].atom_density_bcm, 0.00591035, places=4)
        self.assertEqual(f"{rows['O16'].atom_density_bcm:.4f}", "0.0333")
        self.assertEqual(f"{rows['F19'].atom_density_bcm:.4f}", "0.0148")
        self.assertEqual(f"{rows['H1'].atom_density_bcm:.3f}", "0.037")


if __name__ == "__main__":
    unittest.main()
