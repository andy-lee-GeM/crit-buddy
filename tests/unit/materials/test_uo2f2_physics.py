import unittest

from critbuddy.core.materials.uo2f2_physics import (
    uranyl_fluoride_density,
    uo2f2_density,
    uo2f2_stoichiometry,
)


class UO2F2PhysicsTests(unittest.TestCase):
    def test_uo2f2_density_tracks_stoichiometry(self):
        stoich = uo2f2_stoichiometry(40.444, enrichment_pct=5.0)
        self.assertAlmostEqual(stoich.density_g_cm3, 1.674943184, places=6)
        self.assertAlmostEqual(
            uo2f2_density(40.444, enrichment_pct=5.0),
            stoich.density_g_cm3,
            places=9,
        )

    def test_uo2f2_density_depends_on_enrichment(self):
        self.assertAlmostEqual(uo2f2_density(40.444, enrichment_pct=5.0), 1.674943184, places=6)
        self.assertAlmostEqual(uo2f2_density(40.444, enrichment_pct=10.0), 1.674564482, places=6)

    def test_uranyl_fluoride_density_uses_hydrated_salt_branch_below_h_over_u_4(self):
        self.assertAlmostEqual(uranyl_fluoride_density(2.0, Mu=238.0), 4.32, places=9)

    def test_uranyl_fluoride_density_uses_aqueous_branch_at_h_over_u_4_and_above(self):
        self.assertAlmostEqual(uranyl_fluoride_density(5.0, Mu=238.0), 2.9270836408001024, places=9)

    def test_uo2f2_density_matches_piecewise_model_in_hydrated_region(self):
        density = uo2f2_density(3.5, enrichment_pct=5.0)
        self.assertAlmostEqual(density, 5.478683412, places=6)

    def test_uo2f2_density_matches_piecewise_model_in_aqueous_region(self):
        density = uo2f2_density(30.0, enrichment_pct=5.0)
        self.assertAlmostEqual(density, 1.882956359, places=6)

    def test_uo2f2_density_varies_smoothly_with_enrichment(self):
        density = uo2f2_density(40.444, enrichment_pct=15.0)
        self.assertAlmostEqual(density, 1.674186264, places=6)

    def test_uo2f2_density_rejects_negative_h_to_u(self):
        with self.assertRaises(ValueError):
            uo2f2_stoichiometry(-1.0, enrichment_pct=5.0)


if __name__ == "__main__":
    unittest.main()
