"""Integration test for cylinder-array model."""

import unittest
from pathlib import Path

import openmc

from critbuddy.core.materials.uo2f2_physics import uo2f2_density
from critbuddy.core.template_loader import load_model_class, load_model_module

ROOT = Path(__file__).resolve().parents[3]
MODELS_ROOT = ROOT / "models"


class CylinderArrayModelTests(unittest.TestCase):
    """Test that cylinder-array builds correctly."""

    def test_model_imports_successfully(self):
        template = load_model_class("cylinder-array")
        model = load_model_module(MODELS_ROOT / "cylinder-array")

        self.assertIsNotNone(template)
        self.assertIsNotNone(model.build_model)

    def test_template_derives_expected_geometry(self):
        template = load_model_class("cylinder-array")

        derived = template.derive_params(
            {
                "inner_radius_cm": 11.70,
                "water_film_thickness_cm": 1.0,
                "wall_thickness_cm": 0.3175,
                "vessel_height_cm": 100.0,
                "fill_height_cm": 20.0,
                "num_cylinders_x": 3,
                "num_cylinders_y": 2,
                "num_cylinders_z": 4,
                "wall_to_wall_gap_cm": 1.0,
            }
        )

        self.assertAlmostEqual(derived["OUTER_RADIUS_CM"], 13.0175, places=6)
        self.assertAlmostEqual(derived["OUTER_DIAMETER_CM"], 26.035, places=6)
        self.assertAlmostEqual(derived["OUTER_HEIGHT_CM"], 100.635, places=6)
        self.assertAlmostEqual(derived["PITCH_X_CM"], 27.035, places=6)
        self.assertAlmostEqual(derived["PITCH_Y_CM"], 101.635, places=6)
        self.assertAlmostEqual(derived["PITCH_Z_CM"], 27.035, places=6)
        self.assertAlmostEqual(derived["ARRAY_X_CM"], 80.105, places=6)
        self.assertAlmostEqual(derived["ARRAY_Y_CM"], 202.27, places=6)
        self.assertAlmostEqual(derived["ARRAY_Z_CM"], 107.14, places=6)
        self.assertAlmostEqual(derived["EDGE_MODERATOR_THICKNESS_CM"], 50.0, places=6)
        self.assertAlmostEqual(derived["TOTAL_X_CM"], 180.105, places=6)
        self.assertAlmostEqual(derived["TOTAL_Y_CM"], 302.27, places=6)
        self.assertAlmostEqual(derived["TOTAL_Z_CM"], 207.14, places=6)
        self.assertEqual(derived["TOTAL_CYLINDERS"], 24)
        self.assertEqual(derived["FISSILE_MATERIAL"], "uo2f2")

    def test_fill_fraction_percent_overrides_fill_height(self):
        template = load_model_class("cylinder-array")

        derived = template.derive_params(
            {
                "vessel_height_cm": 200.0,
                "fill_height_cm": 20.0,
                "fill_fraction_percent": 25.0,
            }
        )

        self.assertAlmostEqual(derived["FILL_HEIGHT_CM"], 50.0, places=6)
        self.assertAlmostEqual(derived["FILL_FRACTION"], 0.25, places=6)
        self.assertAlmostEqual(derived["FILL_FRACTION_PERCENT"], 25.0, places=6)

    def test_template_accepts_explicit_uf6_material_selection(self):
        template = load_model_class("cylinder-array")

        derived = template.derive_params(
            {
                "fissile_material": "uf6",
                "fissile_density_g_cm3": 0.0127,
            }
        )

        self.assertEqual(derived["FISSILE_MATERIAL"], "uf6")
        self.assertAlmostEqual(derived["FISSILE_DENSITY_G_CM3"], 0.0127, places=6)

    def test_model_builds_with_defaults(self):
        template = load_model_class("cylinder-array")
        model = load_model_module(MODELS_ROOT / "cylinder-array")

        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        self.assertEqual(len(materials), 4)
        materials_by_name = {mat.name: mat for mat in materials}
        self.assertEqual(set(materials_by_name), {"Fuel", "Wall", "Water", "Air"})

        fuel = materials_by_name["Fuel"]
        self.assertAlmostEqual(
            fuel.density,
            uo2f2_density(h_to_u=all_params["H_TO_U"], enrichment_pct=all_params["ENRICHMENT_PCT"]),
            places=6,
        )

        self.assertEqual(dims["NUM_CYLINDERS_X"], 1)
        self.assertEqual(dims["NUM_CYLINDERS_Y"], 1)
        self.assertEqual(dims["NUM_CYLINDERS_Z"], 1)
        self.assertAlmostEqual(dims["EDGE_MODERATOR_THICKNESS_CM"], 50.0, places=6)

        root_cells = list(geometry.root_universe.cells.values())
        self.assertEqual(len(root_cells), 2)
        cells_by_name = {cell.name: cell for cell in root_cells}
        self.assertIn("array_region", cells_by_name)
        self.assertIn("edge_moderator", cells_by_name)
        self.assertIsInstance(cells_by_name["array_region"].fill, openmc.RectLattice)
        self.assertEqual(cells_by_name["edge_moderator"].fill.name, "Water")

        unit_universe = cells_by_name["array_region"].fill.universes[0][0][0]
        unit_cell_names = {cell.name for cell in unit_universe.cells.values()}
        self.assertEqual(
            unit_cell_names,
            {
                "fuel",
                "headspace",
                "water_annulus",
                "material_wall",
                "top_cap",
                "bottom_cap",
                "local_air",
            },
        )

    def test_model_builds_with_explicit_uf6(self):
        template = load_model_class("cylinder-array")
        model = load_model_module(MODELS_ROOT / "cylinder-array")

        params = {
            "fissile_material": "uf6",
            "fissile_density_g_cm3": 0.0127,
        }
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        fuel = {mat.name: mat for mat in materials}["Fuel"]
        self.assertAlmostEqual(fuel.density, 0.0127, places=6)
        self.assertEqual(dims["FISSILE_MATERIAL"], "uf6")
        self.assertEqual(len(list(geometry.root_universe.cells.values())), 2)

    def test_boundary_mapping_uses_user_axes(self):
        template = load_model_class("cylinder-array")
        model = load_model_module(MODELS_ROOT / "cylinder-array")

        params = {
            "x_boundary_type": "reflective",
            "y_boundary_type": "vacuum",
            "z_boundary_type": "reflective",
        }
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        _, geometry, _ = model.build_model(all_params)

        surfaces = geometry.get_all_surfaces()
        named = {surface.name: surface for surface in surfaces.values()}

        self.assertEqual(named["x_min"].boundary_type, "reflective")
        self.assertEqual(named["x_max"].boundary_type, "reflective")
        self.assertEqual(named["vertical_min"].boundary_type, "vacuum")
        self.assertEqual(named["vertical_max"].boundary_type, "vacuum")
        self.assertEqual(named["depth_min"].boundary_type, "reflective")
        self.assertEqual(named["depth_max"].boundary_type, "reflective")

    def test_fill_height_cannot_exceed_vessel_height(self):
        template = load_model_class("cylinder-array")

        with self.assertRaises(ValueError):
            template.derive_params(
                {
                    "vessel_height_cm": 20.0,
                    "fill_height_cm": 25.0,
                }
            )

    def test_edge_moderator_thickness_cannot_be_negative(self):
        template = load_model_class("cylinder-array")

        with self.assertRaises(ValueError):
            template.derive_params({"edge_moderator_thickness_cm": -1.0})

    def test_settings_creation(self):
        template = load_model_class("cylinder-array")
        model = load_model_module(MODELS_ROOT / "cylinder-array")

        params = {
            "num_cylinders_x": 3,
            "num_cylinders_y": 2,
            "num_cylinders_z": 3,
        }
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)
        settings = model.create_settings(all_params, dims)

        self.assertEqual(settings.particles, template.get_simulation_params()["PARTICLES"])
        self.assertEqual(settings.batches, template.get_simulation_params()["BATCHES"])
        self.assertEqual(settings.inactive, template.get_simulation_params()["INACTIVE"])
        self.assertIsNotNone(settings.source)


if __name__ == "__main__":
    unittest.main()
