"""Integration test for pipe-cross-model."""

import unittest
from pathlib import Path

import openmc
from critbuddy.core.template_loader import load_model_class, load_model_module

ROOT = Path(__file__).resolve().parents[3]
MODELS_ROOT = ROOT / "models"


class PipeCrossModelTests(unittest.TestCase):
    """Test that pipe-cross-model builds correctly."""

    def test_model_imports_successfully(self):
        """Test that the model module can be imported."""
        template = load_model_class("pipe-cross-model")
        model = load_model_module(MODELS_ROOT / "pipe-cross-model")

        self.assertIsNotNone(template)
        self.assertIsNotNone(model.build_model)

    def test_model_builds_with_defaults(self):
        """Test that model builds with default parameters."""
        template = load_model_class("pipe-cross-model")
        model = load_model_module(MODELS_ROOT / "pipe-cross-model")
        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        # Verify materials created
        self.assertEqual(len(materials), 4)
        mat_names = {mat.name for mat in materials}
        self.assertIn("Fuel", mat_names)
        self.assertIn("Gas", mat_names)
        self.assertIn("Wall", mat_names)
        self.assertIn("Water", mat_names)

        # Verify geometry dimensions match default xz mode
        self.assertAlmostEqual(dims["PIPE_OUTER_RADIUS_CM"], 5.715, places=4)
        self.assertAlmostEqual(dims["GAS_CORE_RADIUS_CM"], 4.4102, places=4)
        self.assertAlmostEqual(dims["FUEL_OUTER_RADIUS_CM"], 5.4102, places=4)
        self.assertEqual(dims["CROSS_MODE"], "xz")

        # Verify cells created
        cells = list(geometry.root_universe.cells.values())
        self.assertGreater(len(cells), 0)

        # Check for xz mode cells (7 cells: z_gas, z_fuel, z_wall, x_gas, x_fuel, x_wall, moderator)
        cell_names = {cell.name for cell in cells}
        self.assertIn("z_gas_core", cell_names)
        self.assertIn("z_fuel", cell_names)
        self.assertIn("z_wall", cell_names)
        self.assertIn("x_gas_core", cell_names)
        self.assertIn("x_fuel", cell_names)
        self.assertIn("x_wall", cell_names)
        self.assertIn("moderator", cell_names)
        self.assertEqual(len(cells), 7)

    def test_xyz_cross_mode(self):
        """Test that xyz crossing mode creates all three pipes."""
        template = load_model_class("pipe-cross-model")
        model = load_model_module(MODELS_ROOT / "pipe-cross-model")
        params = {"cross_mode": "xyz"}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        # Verify xyz mode
        self.assertEqual(dims["CROSS_MODE"], "xyz")

        # Check for xyz mode cells (10 cells: 3 gas + 3 fuel + 3 wall + 1 moderator)
        cells = list(geometry.root_universe.cells.values())
        cell_names = {cell.name for cell in cells}
        self.assertIn("y_gas_core", cell_names)
        self.assertIn("y_fuel", cell_names)
        self.assertIn("y_wall", cell_names)
        self.assertEqual(len(cells), 10)

    def test_gap_zero_reference_case(self):
        """Test the gap=0 reference case matching MCNP deck."""
        template = load_model_class("pipe-cross-model")
        model = load_model_module(MODELS_ROOT / "pipe-cross-model")

        # Parameters matching the MCNP reference deck in REFERENCE_ANALYSIS.md
        params = {
            "cross_mode": "xz",
            "enrichment_pct": 20.19,
            "pipe_outer_radius_cm": 5.715,
            "pipe_wall_thickness_cm": 0.3048,
            "gas_core_radius_cm": 4.4102,
            "fuel_outer_radius_cm": 5.4102,
            "uf6_density_g_cm3": 0.0127,
            "uo2f2_density_g_cm3": 6.37,
            "separation_cm": 0.0,  # Gap = 0 case
            "wall_material": "aluminum",
            "moderator_density_g_cm3": 1.0,
        }

        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        # Verify gap = 0 geometry
        self.assertAlmostEqual(dims["SEPARATION_CM"], 0.0, places=6)
        center_offset = 2.0 * 5.715 + 0.0  # 2 * outer_radius + separation
        self.assertAlmostEqual(dims["PIPE_CENTER_OFFSET_CM"], center_offset, places=3)
        self.assertAlmostEqual(dims["PIPE_CENTER_OFFSET_CM"], 11.43, places=2)

        # Verify enrichment matches MCNP reference
        self.assertAlmostEqual(all_params["ENRICHMENT_PCT"], 20.19, places=2)

    def test_reflective_boundaries(self):
        """Test that reflective boundaries are set correctly."""
        template = load_model_class("pipe-cross-model")
        model = load_model_module(MODELS_ROOT / "pipe-cross-model")
        params = {
            "x_boundary_type": "reflective",
            "y_boundary_type": "reflective",
            "z_boundary_type": "reflective",
        }
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        surfaces = geometry.get_all_surfaces()
        boundary_surfaces = [s for s in surfaces.values() if s.boundary_type == "reflective"]

        # Should have 6 reflective surfaces (x_min, x_max, y_min, y_max, z_min, z_max)
        self.assertGreaterEqual(len(boundary_surfaces), 6)

    def test_standard_nps_pipe_size(self):
        """Test that NPS sizing populates the pipe dimensions automatically."""
        template = load_model_class("pipe-cross-model")
        params = {
            "pipe_size": "4",
            "separation_cm": 7.0,
        }

        errors = template.validate_params(params)
        self.assertEqual(errors, [])

        derived = template.derive_params(template.apply_defaults(params))
        self.assertEqual(derived["PIPE_SIZE"], "4")
        self.assertAlmostEqual(derived["PIPE_OUTER_RADIUS_CM"], 5.715, places=3)
        self.assertAlmostEqual(derived["PIPE_WALL_THICKNESS_CM"], 0.305, places=3)
        self.assertAlmostEqual(derived["PIPE_INNER_RADIUS_CM"], 5.41, places=2)

    def test_settings_creation(self):
        """Test that OpenMC settings are created correctly."""
        template = load_model_class("pipe-cross-model")
        model = load_model_module(MODELS_ROOT / "pipe-cross-model")
        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)
        settings = model.create_settings(all_params, dims)

        self.assertEqual(settings.run_mode, "eigenvalue")
        self.assertEqual(settings.particles, 4800)
        self.assertEqual(settings.batches, 200)
        self.assertEqual(settings.inactive, 50)
        self.assertIsNotNone(settings.source)

        # Verify source is at origin
        self.assertGreater(len(settings.source), 0)
        source_space = settings.source[0].space
        self.assertIsInstance(source_space, openmc.stats.Point)

    def test_plots_creation(self):
        """Test that geometry plots are created."""
        template = load_model_class("pipe-cross-model")
        model = load_model_module(MODELS_ROOT / "pipe-cross-model")
        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)
        plots, legend = model.create_plots(dims, materials)

        self.assertGreater(len(plots), 0)
        plot_names = [p.name for p in plots]
        self.assertIn("xy", plot_names)
        self.assertIn("xz", plot_names)

    def test_asymmetric_boundary_box(self):
        """Test that the boundary box is asymmetric as in MCNP reference."""
        template = load_model_class("pipe-cross-model")
        params = {
            "cross_mode": "xz",
            "separation_cm": 0.0,
        }
        derived = template.derive_params(params)

        # For xz mode, x should be smaller than y
        x_extent = derived["X_MAX_CM"] - derived["X_MIN_CM"]
        y_extent = derived["Y_MAX_CM"] - derived["Y_MIN_CM"]

        self.assertLess(x_extent, y_extent)


if __name__ == "__main__":
    unittest.main()
