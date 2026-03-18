import math
import unittest
from pathlib import Path

import openmc
from critbuddy.core.template_loader import load_template_class, load_template_module


ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ROOT / "templates"


class CylinderUnitCellModelTests(unittest.TestCase):
    def _base_params(self) -> dict:
        return {
            "enrichment": 20.0,
            "fissile_material": "uo2f2",
            "h_to_u": 5.0,
            "fill_fraction": 0.3,
            "radius_cm": 11.7,
            "height_cm": 100.0,
            "wall_thickness_cm": 1.3175,
            "wall_material": "steel",
            "rows": 1,
            "cols": 1,
            "layers": 1,
            "gap_cm": 1.0,
            "environment_material": "humid_air",
            "environment_density": 0.0011,
            "void_material": "humid_air",
            "boundary_type": "reflective",
            "reflector_thickness_cm": 100.0,
        }

    def test_cylinder_unit_cell_builds_expected_geometry(self):
        template = load_template_class("cylinder")
        template_module = load_template_module(TEMPLATES / "cylinder")

        params = template.apply_defaults(self._base_params())
        errors = template.validate_params(params)
        self.assertEqual(errors, [])

        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = template_module.build_model(all_params)
        self.assertIsNotNone(materials)
        self.assertEqual(dims["fill_fraction"], 0.3)
        self.assertTrue(math.isclose(derived["INNER_RADIUS"], 11.7, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["OUTER_RADIUS"], 13.0175, rel_tol=0.0, abs_tol=1.0e-9))
        self.assertTrue(math.isclose(derived["FISSILE_HEIGHT"], 30.0, rel_tol=0.0, abs_tol=1.0e-9))

        cell_names = sorted(cell.name for cell in geometry.root_universe.cells.values())
        self.assertEqual(cell_names, ["CapBot_0_0_0", "CapTop_0_0_0", "Environment", "UF6_0_0_0", "Void_0_0_0", "Wall_0_0_0"])

        surfaces = geometry.get_all_surfaces()
        named = {surface.name: surface for surface in surfaces.values()}

        self.assertEqual(named["x_min"].boundary_type, "reflective")
        self.assertEqual(named["x_max"].boundary_type, "reflective")
        self.assertEqual(named["y_min"].boundary_type, "reflective")
        self.assertEqual(named["y_max"].boundary_type, "reflective")
        self.assertEqual(named["z_min"].boundary_type, "reflective")
        self.assertEqual(named["z_max"].boundary_type, "reflective")

        cells_by_name = {cell.name: cell for cell in geometry.root_universe.cells.values()}
        environment_material = cells_by_name["Environment"].fill
        headspace_material = cells_by_name["Void_0_0_0"].fill
        self.assertEqual(environment_material.name, headspace_material.name)
        self.assertEqual(environment_material.density_units, headspace_material.density_units)
        self.assertAlmostEqual(environment_material.density, headspace_material.density, places=10)


if __name__ == "__main__":
    unittest.main()
