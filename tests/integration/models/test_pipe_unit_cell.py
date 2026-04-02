"""Integration test for pipe-unit-cell model."""

import math
import unittest
from pathlib import Path

import openmc
from critbuddy.core.template_loader import load_model_class, load_model_module

ROOT = Path(__file__).resolve().parents[3]
MODELS_ROOT = ROOT / "models"


class PipeUnitCellModelTests(unittest.TestCase):
    """Test that pipe-unit-cell model builds correctly."""

    def test_model_imports_successfully(self):
        """Test that the model module can be imported."""
        template = load_model_class("pipe-unit-cell")
        model = load_model_module(MODELS_ROOT / "pipe-unit-cell")

        self.assertIsNotNone(template)
        self.assertIsNotNone(model.build_model)

    def test_model_builds_with_defaults(self):
        """Test that model builds with default parameters."""
        template = load_model_class("pipe-unit-cell")
        model = load_model_module(MODELS_ROOT / "pipe-unit-cell")
        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        # Verify materials created
        self.assertEqual(len(materials), 3)
        mat_names = {mat.name for mat in materials}
        self.assertIn("UO2F2_Solution", mat_names)
        self.assertIn("UF6_Gas", mat_names)
        self.assertIn("Aluminum", mat_names)

        # Verify geometry dimensions match inputs
        self.assertAlmostEqual(dims["PIPE_OUTER_RADIUS_CM"], 5.715, places=4)
        self.assertAlmostEqual(dims["SOLUTION_RADIUS_CM"], 4.4102, places=4)
        self.assertAlmostEqual(dims["FILL_FRACTION"], 1.0, places=4)

        # Verify cells created
        cells = list(geometry.root_universe.cells.values())
        self.assertGreater(len(cells), 0)

        cell_names = {cell.name for cell in cells}
        self.assertIn("uo2f2_solution", cell_names)
        self.assertIn("pipe_wall", cell_names)
        self.assertIn("gas_gap", cell_names)

    def test_model_with_partial_fill(self):
        """Test that partial fill fraction works correctly."""
        template = load_model_class("pipe-unit-cell")
        model = load_model_module(MODELS_ROOT / "pipe-unit-cell")
        params = {"fill_fraction": 0.5}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        # Verify fill fraction
        self.assertAlmostEqual(dims["FILL_FRACTION"], 0.5, places=4)
        self.assertAlmostEqual(dims["FILL_HEIGHT_CM"], 17.43 * 0.5, places=2)

        # Verify headspace cell exists
        cell_names = {cell.name for cell in geometry.root_universe.cells.values()}
        self.assertIn("headspace", cell_names)

    def test_standard_nps_pipe_size_derives_geometry(self):
        """Test that NPS sizing populates the pipe dimensions automatically."""
        template = load_model_class("pipe-unit-cell")
        params = {
            "pipe_size": "4",
            "solution_radius_cm": None,
            "solution_gap_cm": 1.0,
        }

        errors = template.validate_params(params)
        self.assertEqual(errors, [])

        derived = template.derive_params(template.apply_defaults(params))
        self.assertEqual(derived["PIPE_SIZE"], "4")
        self.assertAlmostEqual(derived["PIPE_OUTER_RADIUS_CM"], 5.715, places=3)
        self.assertAlmostEqual(derived["PIPE_WALL_THICKNESS_CM"], 0.305, places=3)
        self.assertAlmostEqual(derived["PIPE_INNER_RADIUS_CM"], 5.41, places=2)
        self.assertAlmostEqual(derived["SOLUTION_GAP_CM"], 1.0, places=6)
        self.assertAlmostEqual(
            derived["SOLUTION_RADIUS_CM"],
            derived["PIPE_INNER_RADIUS_CM"] - 1.0,
            places=6,
        )
        self.assertAlmostEqual(
            derived["TOTAL_FUEL_VOLUME_CM3"],
            math.pi * derived["SOLUTION_RADIUS_CM"] ** 2 * derived["PIPE_HEIGHT_CM"],
            places=6,
        )
        self.assertAlmostEqual(
            derived["FILL_VOLUME_CM3"],
            derived["TOTAL_FUEL_VOLUME_CM3"],
            places=6,
        )

    def test_reflective_boundaries(self):
        """Test that reflective boundaries are set correctly."""
        template = load_model_class("pipe-unit-cell")
        model = load_model_module(MODELS_ROOT / "pipe-unit-cell")
        params = {"boundary_type": "reflective"}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        surfaces = geometry.get_all_surfaces()
        boundary_surfaces = [s for s in surfaces.values() if s.boundary_type == "reflective"]

        # Should have at least z_bottom and z_top reflective
        self.assertGreaterEqual(len(boundary_surfaces), 2)

    def test_vacuum_boundaries(self):
        """Test that vacuum boundaries work."""
        template = load_model_class("pipe-unit-cell")
        model = load_model_module(MODELS_ROOT / "pipe-unit-cell")
        params = {"boundary_type": "vacuum"}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        surfaces = geometry.get_all_surfaces()
        vacuum_surfaces = [s for s in surfaces.values() if s.boundary_type == "vacuum"]

        # Should have vacuum boundaries
        self.assertGreaterEqual(len(vacuum_surfaces), 2)

    def test_settings_creation(self):
        """Test that OpenMC settings are created correctly."""
        template = load_model_class("pipe-unit-cell")
        model = load_model_module(MODELS_ROOT / "pipe-unit-cell")
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

    def test_plots_creation(self):
        """Test that geometry plots are created."""
        template = load_model_class("pipe-unit-cell")
        model = load_model_module(MODELS_ROOT / "pipe-unit-cell")
        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)
        plots, legend = model.create_plots(dims, materials)

        self.assertGreater(len(plots), 0)
        self.assertIn("xy", [p.name for p in plots])
        self.assertIn("xz", [p.name for p in plots])


if __name__ == "__main__":
    unittest.main()
