import unittest

from critbuddy.analysis import compute_uo2f2_inventory, compute_uf6_inventory
from critbuddy.core.materials.uo2f2_physics import uo2f2_stoichiometry


class UF6InventoryTests(unittest.TestCase):
    def test_compute_uf6_inventory_converts_volume_to_mass(self):
        inventory = compute_uf6_inventory(
            total_volume_cm3=1000.0,
            fill_fraction=0.25,
            density_g_cm3=5.09,
        )

        self.assertAlmostEqual(inventory.total_volume_cm3, 1000.0, places=9)
        self.assertAlmostEqual(inventory.total_volume_l, 1.0, places=9)
        self.assertAlmostEqual(inventory.filled_volume_cm3, 250.0, places=9)
        self.assertAlmostEqual(inventory.filled_volume_l, 0.25, places=9)
        self.assertAlmostEqual(inventory.bulk_density_g_cm3, 5.09, places=9)
        self.assertAlmostEqual(inventory.uf6_mass_kg, 5.09 * 250.0 / 1000.0, places=9)

    def test_compute_uf6_inventory_rejects_non_positive_total_volume(self):
        with self.assertRaises(ValueError):
            compute_uf6_inventory(
                total_volume_cm3=0.0,
                fill_fraction=0.25,
            )


class UO2F2InventoryTests(unittest.TestCase):
    def test_compute_uo2f2_inventory_converts_volume_to_component_masses(self):
        inventory = compute_uo2f2_inventory(
            total_volume_cm3=1000.0,
            fill_fraction=0.25,
            h_to_u=5.0,
            enrichment_pct=20.0,
        )

        stoich = uo2f2_stoichiometry(h_to_u=5.0, enrichment_pct=20.0)

        self.assertAlmostEqual(inventory.total_volume_cm3, 1000.0, places=9)
        self.assertAlmostEqual(inventory.total_volume_l, 1.0, places=9)
        self.assertAlmostEqual(inventory.filled_volume_cm3, 250.0, places=9)
        self.assertAlmostEqual(inventory.filled_volume_l, 0.25, places=9)
        self.assertAlmostEqual(inventory.bulk_density_g_cm3, stoich.density_g_cm3, places=9)
        self.assertAlmostEqual(
            inventory.uo2f2_component_density_g_cm3,
            stoich.uo2f2_component_density_g_cm3,
            places=9,
        )
        self.assertAlmostEqual(
            inventory.h2o_component_density_g_cm3,
            stoich.h2o_component_density_g_cm3,
            places=9,
        )
        self.assertAlmostEqual(
            inventory.wet_solution_mass_kg,
            stoich.density_g_cm3 * 250.0 / 1000.0,
            places=9,
        )
        self.assertAlmostEqual(
            inventory.uo2f2_mass_kg,
            stoich.uo2f2_component_density_g_cm3 * 250.0 / 1000.0,
            places=9,
        )
        self.assertAlmostEqual(
            inventory.water_mass_kg,
            stoich.h2o_component_density_g_cm3 * 250.0 / 1000.0,
            places=9,
        )

    def test_compute_uo2f2_inventory_rejects_non_positive_total_volume(self):
        with self.assertRaises(ValueError):
            compute_uo2f2_inventory(
                total_volume_cm3=0.0,
                fill_fraction=0.25,
                h_to_u=5.0,
                enrichment_pct=20.0,
            )


if __name__ == "__main__":
    unittest.main()
