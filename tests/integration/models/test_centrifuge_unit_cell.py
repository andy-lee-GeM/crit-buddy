import math
import unittest
from pathlib import Path

import openmc
from critbuddy.core.template_loader import load_model_class, load_model_module
from tests._openmc_plot_assertions import render_openmc_plots


ROOT = Path(__file__).resolve().parents[3]
MODELS = ROOT / "models"
VISUALIZATIONS = ROOT / "tests" / "_visualizations"


class CentrifugeUnitCellModelTests(unittest.TestCase):
    def test_centrifuge_unit_cell_builds_expected_geometry(self):
        mcnp_dir = MODELS / "centrifuge-unit-cell" / "mcnp"

        self.assertTrue((mcnp_dir / "model.inp").exists())
        self.assertFalse((mcnp_dir / "original.inp").exists())
        self.assertFalse((mcnp_dir / "stamped.inp").exists())
        template = load_model_class("centrifuge-unit-cell")
        module = load_model_module(MODELS / "centrifuge-unit-cell")

        params = template.apply_defaults(
            {
                "fill_z_cm": 20.0,
                "source_z_cm": 10.0,
                "z_boundary_type": "reflective",
            }
        )
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

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

        openmc.reset_auto_ids()
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
                "material_wall",
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
        fuel = materials_by_name["Fuel"]
        wall = materials_by_name["Wall"]
        water = materials_by_name["Water"]
        air = materials_by_name["Air"]

        self.assertAlmostEqual(fuel.density, 4.33, places=10)
        self.assertEqual(fuel.density_units, "g/cm3")
        self.assertAlmostEqual(wall.density, 8.0, places=10)
        self.assertEqual(wall.density_units, "g/cm3")
        self.assertAlmostEqual(water.density, 1.0, places=10)
        self.assertEqual(water.density_units, "g/cm3")
        self.assertAlmostEqual(air.density, 3.3e-02, places=10)
        self.assertEqual(air.density_units, "atom/b-cm")

        fuel_nuclides = {nuc.name: (nuc.percent, nuc.percent_type) for nuc in fuel.nuclides}
        self.assertEqual(
            fuel_nuclides,
            {
                "U235": (0.001496, "ao"),
                "U238": (0.00591035, "ao"),
                "O16": (0.0333, "ao"),
                "F19": (0.0148, "ao"),
                "H1": (0.037, "ao"),
            },
        )

        wall_nuclides = {nuc.name: (nuc.percent, nuc.percent_type) for nuc in wall.nuclides}
        self.assertEqual(
            wall_nuclides,
            {
                "Ni58": (0.0017, "ao"),
                "Fe56": (0.0777, "ao"),
                "Mn55": (4.30e-04, "ao"),
                "Mo96": (2.08e-04, "ao"),
                "Cr52": (0.0138, "ao"),
            },
        )

        air_nuclides = {nuc.name: (nuc.percent, nuc.percent_type) for nuc in air.nuclides}
        self.assertEqual(
            air_nuclides,
            {
                "N14": (3.9e-05, "ao"),
                "O16": (1.05e-05, "ao"),
                "Ar40": (2.4e-04, "ao"),
                "H1": (1.1e-06, "ao"),
            },
        )

        plots, legend = module.create_plots(dims, materials)
        render_openmc_plots(
            materials=materials,
            geometry=geometry,
            plots=plots,
            color_legend=legend,
            output_dir=VISUALIZATIONS / "centrifuge_unit_cell",
            expected_plot_names=["xy", "xz"],
        )


if __name__ == "__main__":
    unittest.main()
