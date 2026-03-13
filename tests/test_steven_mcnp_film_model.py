import math
import unittest
from pathlib import Path

from critbuddy.core.template_loader import load_template_class, load_template_module


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class StevenMCNPFilmModelTests(unittest.TestCase):
    def test_derive_params_matches_current_mcnp_deck(self):
        template = load_template_class("steven_mcnp_film")
        params = template.apply_defaults({"fill_z_cm": 20.0, "source_z_cm": 10.0})
        errors = template.validate_params(params)
        self.assertEqual(errors, [])

        derived = template.derive_params(params)

        self.assertTrue(math.isclose(derived["FILL_Z_CM"], 20.0, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["FILL_HEIGHT_CM"], 20.0, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["FILL_FRACTION"], 0.2, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["FUEL_RADIUS_CM"], 11.70, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["WATER_OUTER_RADIUS_CM"], 12.70, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["OUTER_RADIUS_CM"], 13.0175, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertEqual(derived["Z_BOUNDARY_BOTTOM_CM"], -50.0)
        self.assertEqual(derived["Z_BOUNDARY_TOP_CM"], 150.0)
        self.assertEqual(derived["Z_CAP_BOTTOM_CM"], -0.3175)
        self.assertEqual(derived["Z_CAP_TOP_CM"], 100.3175)

    def test_build_model_includes_caps_and_atom_density_air(self):
        template = load_template_class("steven_mcnp_film")
        module = load_template_module(TEMPLATES / "steven_mcnp_film")

        params = template.apply_defaults({"fill_z_cm": 20.0, "source_z_cm": 10.0})
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        materials, geometry, dims = module.build_model(all_params)
        self.assertEqual(dims["FILL_HEIGHT_CM"], 20.0)

        cells_by_name = {cell.name: cell for cell in geometry.root_universe.cells.values()}
        self.assertEqual(
            sorted(cells_by_name),
            [
                "bottom_cap",
                "bottom_internal_air",
                "fuel",
                "headspace",
                "main_wall",
                "outer_air",
                "top_cap",
                "top_internal_air",
                "water_annulus",
            ],
        )

        surfaces = geometry.get_all_surfaces()
        named_surfaces = {surface.name: surface for surface in surfaces.values()}
        self.assertEqual(named_surfaces["x_min"].boundary_type, "reflective")
        self.assertEqual(named_surfaces["x_max"].boundary_type, "reflective")
        self.assertEqual(named_surfaces["y_min"].boundary_type, "reflective")
        self.assertEqual(named_surfaces["y_max"].boundary_type, "reflective")
        self.assertEqual(named_surfaces["z_min"].boundary_type, "reflective")
        self.assertEqual(named_surfaces["z_max"].boundary_type, "reflective")

        materials_by_name = {material.name: material for material in materials}
        air = materials_by_name["Steven_MCNP_M4_Air"]
        self.assertAlmostEqual(air.density, 3.3e-02, places=10)
        self.assertEqual(air.density_units, "atom/b-cm")


if __name__ == "__main__":
    unittest.main()
