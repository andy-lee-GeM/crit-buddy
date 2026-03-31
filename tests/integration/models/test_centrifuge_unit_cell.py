"""Integration test for centrifuge-unit-cell model."""

import unittest
from pathlib import Path

import openmc
from critbuddy.core.materials.uo2f2_physics import uo2f2_density
from critbuddy.core.template_loader import load_model_class, load_model_module

ROOT = Path(__file__).resolve().parents[3]
MODELS_ROOT = ROOT / "models"


class CentrifugeUnitCellTests(unittest.TestCase):
    """Test that centrifuge-unit-cell builds correctly."""

    def test_model_imports_successfully(self):
        """Test that the model module can be imported."""
        template = load_model_class("centrifuge-unit-cell")
        model = load_model_module(MODELS_ROOT / "centrifuge-unit-cell")

        self.assertIsNotNone(template)
        self.assertIsNotNone(model.build_model)

    def test_template_derives_pipe_style_material_keys(self):
        """Test that the template exposes normalized material-selection params."""
        template = load_model_class("centrifuge-unit-cell")

        derived = template.derive_params({})

        self.assertEqual(derived["FISSILE_MATERIAL"], "uo2f2")
        self.assertEqual(derived["WALL_MATERIAL"], "stainless_steel_316")
        self.assertEqual(derived["WATER_MATERIAL"], "water")
        self.assertAlmostEqual(derived["WATER_DENSITY_G_CM3"], 1.0, places=8)
        self.assertEqual(derived["AIR_MATERIAL"], "centrifuge_air")

    def test_model_builds_with_exact_air_and_shared_library_materials(self):
        """Test the current parity path: shared fuel/wall/water plus exact MCNP air."""
        template = load_model_class("centrifuge-unit-cell")
        model = load_model_module(MODELS_ROOT / "centrifuge-unit-cell")
        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        self.assertEqual(len(materials), 4)
        materials_by_name = {mat.name: mat for mat in materials}
        self.assertEqual(set(materials_by_name), {"Fuel", "Wall", "Water", "Air"})

        fuel = materials_by_name["Fuel"]
        wall = materials_by_name["Wall"]
        water = materials_by_name["Water"]
        air = materials_by_name["Air"]

        self.assertAlmostEqual(
            fuel.density,
            uo2f2_density(
                h_to_u=all_params["H_TO_U"],
                enrichment_pct=all_params["ENRICHMENT_PCT"],
            ),
            places=6,
        )
        self.assertEqual(wall.density_units, "g/cm3")
        self.assertAlmostEqual(wall.density, 8.0, places=6)
        self.assertEqual(water.density_units, "g/cm3")
        self.assertAlmostEqual(water.density, 1.0, places=6)

        self.assertEqual(air.density_units, "atom/b-cm")
        self.assertAlmostEqual(air.density, 3.3e-02, places=8)
        self.assertEqual(
            {nuclide.name: nuclide.percent for nuclide in air.nuclides},
            {
                "N14": 3.9e-05,
                "O16": 1.05e-05,
                "Ar40": 2.4e-04,
                "H1": 1.1e-06,
            },
        )

        cells = list(geometry.root_universe.cells.values())
        self.assertEqual(len(cells), 9)
        cell_names = {cell.name for cell in cells}
        self.assertIn("fuel", cell_names)
        self.assertIn("headspace", cell_names)
        self.assertIn("water_annulus", cell_names)
        self.assertIn("material_wall", cell_names)
        self.assertIn("outer_air", cell_names)

        self.assertAlmostEqual(dims["FUEL_RADIUS_CM"], 11.70, places=6)
        self.assertAlmostEqual(dims["OUTER_RADIUS_CM"], 13.0175, places=6)

    def test_invalid_air_material_raises(self):
        """Test that unsupported air material changes fail loudly."""
        template = load_model_class("centrifuge-unit-cell")
        model = load_model_module(MODELS_ROOT / "centrifuge-unit-cell")

        derived = template.derive_params({})
        derived["AIR_MATERIAL"] = "not-a-material"
        all_params = {**derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        with self.assertRaises(ValueError):
            model.build_model(all_params)


if __name__ == "__main__":
    unittest.main()
