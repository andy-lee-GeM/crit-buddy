import math
import unittest
from pathlib import Path

from critbuddy.core.template_loader import load_template_class, load_template_module


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class CylinderUnitCellModelTests(unittest.TestCase):
    def _base_params(self) -> dict:
        return {
            "enrichment": 20.0,
            "fissile_material": "uo2f2",
            "h_to_u": 5.0,
            "fill_fraction": 0.3,
            "R_inner_cm": 12.7,
            "H_inner_cm": 100.0,
            "t_wall_cm": 0.3175,
            "wall_material": "steel",
            "gap_xy_cm": 1.0,
            "t_film_cm": 1.0,
            "film_material": "water",
            "environment_material": "humid_air",
            "environment_density": 0.0011,
            "void_material": "humid_air",
            "x_boundary_type": "reflective",
            "y_boundary_type": "reflective",
            "z_boundary_type": "reflective",
            "z_buffer_lower_cm": 100.0,
            "z_buffer_upper_cm": 100.0,
        }

    def test_derive_params_matches_expected_unit_cell_dimensions(self):
        template = load_template_class("cylinder_unit_cell")
        params = template.apply_defaults(self._base_params())
        errors = template.validate_params(params)
        self.assertEqual(errors, [])

        derived = template.derive_params(params)

        self.assertTrue(math.isclose(derived["R_FISSILE"], 11.7, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["R_OUTER"], 13.0175, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["HALF_PITCH_XY"], 13.5175, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["FISSILE_HEIGHT"], 30.0, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertEqual(derived["Z_OUTER_MIN"], -100.0)
        self.assertEqual(derived["Z_OUTER_MAX"], 200.0)

    def test_build_model_creates_expected_regions_without_end_caps(self):
        template = load_template_class("cylinder_unit_cell")
        template_module = load_template_module(TEMPLATES / "cylinder_unit_cell")

        params = template.apply_defaults(self._base_params())
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        materials, geometry, dims = template_module.build_model(all_params)
        self.assertIsNotNone(materials)
        self.assertEqual(dims["FILL_FRACTION"], 0.3)

        cell_names = sorted(cell.name for cell in geometry.root_universe.cells.values())
        self.assertEqual(cell_names, ["environment", "film", "fissile", "headspace", "wall"])
        self.assertFalse(any("cap" in name for name in cell_names))

        surfaces = geometry.get_all_surfaces()
        named = {surface.name: surface for surface in surfaces.values()}

        self.assertEqual(named["x_min"].boundary_type, "reflective")
        self.assertEqual(named["x_max"].boundary_type, "reflective")
        self.assertEqual(named["y_min"].boundary_type, "reflective")
        self.assertEqual(named["y_max"].boundary_type, "reflective")
        self.assertEqual(named["z_min"].boundary_type, "reflective")
        self.assertEqual(named["z_max"].boundary_type, "reflective")

        cells_by_name = {cell.name: cell for cell in geometry.root_universe.cells.values()}
        environment_material = cells_by_name["environment"].fill
        headspace_material = cells_by_name["headspace"].fill
        self.assertIs(environment_material, headspace_material)


if __name__ == "__main__":
    unittest.main()
