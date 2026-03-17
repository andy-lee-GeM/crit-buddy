import unittest
from pathlib import Path

import openmc
from critbuddy.core.template_loader import load_template_class, load_template_module
from tests._openmc_plot_assertions import render_openmc_plots


ROOT = Path(__file__).resolve().parents[3]
TEMPLATES = ROOT / "templates"
VISUALIZATIONS = ROOT / "tests" / "_visualizations"


class CascadeArrayModelTests(unittest.TestCase):
    def _base_params(self) -> dict:
        return {
            "enrichment": 5.0,
            "fissile_material": "uf6",
            "R_inner_cm": 10.0,
            "H_inner_cm": 20.0,
            "t_wall_cm": 1.0,
            "wall_material": "steel",
            "i": 2,
            "j": 2,
            "k": 2,
            "gap_xy_cm": 4.0,
            "gap_z_cm": 6.0,
            "environment_material": "air",
            "reflector_thickness_cm": 10.0,
        }

    def test_cascade_array_builds_expected_geometry(self):
        template = load_template_class("cascade_array")
        template_module = load_template_module(TEMPLATES / "cascade_array")

        params = self._base_params()
        params = template.apply_defaults(params)
        errors = template.validate_params(params)
        self.assertEqual(errors, [])

        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = template_module.build_model(all_params)

        self.assertIsNotNone(materials)
        self.assertEqual(dims["I"], 2)
        self.assertEqual(dims["J"], 2)
        self.assertEqual(dims["K"], 2)
        self.assertEqual(dims["total_cylinders"], 8)

        cell_names = sorted(cell.name for cell in geometry.root_universe.cells.values())
        self.assertIn("moderator", cell_names)
        self.assertIn("environment_shell", cell_names)
        self.assertEqual(len(cell_names), 34)

        plots, legend = template_module.create_plots(dims, materials)
        render_openmc_plots(
            materials=materials,
            geometry=geometry,
            plots=plots,
            color_legend=legend,
            output_dir=VISUALIZATIONS / "cascade_array",
            expected_plot_names=["xy", "xz", "yz"],
        )


if __name__ == "__main__":
    unittest.main()
