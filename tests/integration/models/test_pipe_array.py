"""Integration test for pipe-array model."""

import unittest
from pathlib import Path

import openmc
from critbuddy.core.template_loader import load_model_class, load_model_module
from critbuddy.solvers.kcode_settings import KCODE_SETTINGS

ROOT = Path(__file__).resolve().parents[3]
MODELS_ROOT = ROOT / "models"


class PipeArrayModelTests(unittest.TestCase):
    """Test that pipe-array model builds correctly."""

    def test_model_imports_successfully(self):
        """Test that the model module can be imported."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")

        self.assertIsNotNone(template)
        self.assertIsNotNone(model.build_model)

    def test_model_builds_with_defaults(self):
        """Test that model builds with default parameters (2-pipe MCNP reference)."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        # Verify materials created
        self.assertEqual(len(materials), 4)
        mat_names = {mat.name for mat in materials}
        self.assertIn("UO2F2_Solution", mat_names)
        self.assertIn("UF6_Gas", mat_names)
        self.assertIn("Aluminum", mat_names)
        self.assertIn("Water", mat_names)

        # Verify default is 2-pipe configuration
        self.assertEqual(dims["N_PIPES"], 2)
        self.assertAlmostEqual(dims["PIPE_PITCH_CM"], 11.43, places=2)

        # Verify cells created (each pipe has 4 cells + water/void)
        cells = list(geometry.root_universe.cells.values())
        self.assertGreater(len(cells), 8)  # At least 2*4 + 1

    def test_mcnp_reference_configuration(self):
        """Test that MCNP reference configuration is correctly set up."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {
            "n_pipes": 2,
            "pipe_pitch_cm": 11.43,
            "include_water": True,
            "boundary_type": "reflective"
        }
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        # Verify MCNP reference dimensions
        self.assertEqual(dims["N_PIPES"], 2)
        self.assertAlmostEqual(dims["PIPE_PITCH_CM"], 11.43, places=2)
        self.assertAlmostEqual(dims["PIPE_OUTER_RADIUS_CM"], 5.715, places=3)
        self.assertEqual(dims["INCLUDE_WATER"], True)

        # Verify pipe centers (MCNP has first at origin, second at +pitch)
        pipe_centers = dims["PIPE_CENTERS_X"]
        self.assertEqual(len(pipe_centers), 2)
        self.assertAlmostEqual(pipe_centers[0], 0.0, places=4)
        self.assertAlmostEqual(pipe_centers[1], 11.43, places=2)

    def test_single_pipe_array(self):
        """Test that array works with single pipe."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {"n_pipes": 1}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        self.assertEqual(dims["N_PIPES"], 1)
        self.assertEqual(len(dims["PIPE_CENTERS_X"]), 1)

        # Should still build successfully
        cells = list(geometry.root_universe.cells.values())
        self.assertGreater(len(cells), 4)

    def test_multi_pipe_array(self):
        """Test array with more than 2 pipes."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {"n_pipes": 4, "pipe_pitch_cm": 20.0}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        self.assertEqual(dims["N_PIPES"], 4)
        self.assertEqual(len(dims["PIPE_CENTERS_X"]), 4)

        # Each pipe should have 4 cells (solution, headspace, gap, wall) + water/void
        cells = list(geometry.root_universe.cells.values())
        self.assertGreaterEqual(len(cells), 4 * 4 + 1)

    def test_edge_spacing_calculation(self):
        """Test that edge spacing is calculated correctly."""
        template = load_model_class("pipe-array")
        params = {
            "pipe_pitch_cm": 20.0,
            "pipe_outer_radius_cm": 5.0
        }
        derived = template.derive_params(params)

        # Edge spacing = pitch - 2*radius
        expected_spacing = 20.0 - 2 * 5.0
        self.assertAlmostEqual(derived["EDGE_SPACING_CM"], expected_spacing, places=4)

    def test_edge_spacing_input_overrides_pitch(self):
        """Test that edge spacing can drive pitch for NPS-based sweeps."""
        template = load_model_class("pipe-array")
        params = {
            "pipe_size": "4",
            "edge_spacing_cm": 5.08,
            "solution_radius_cm": None,
        }

        errors = template.validate_params(params)
        self.assertEqual(errors, [])

        derived = template.derive_params(template.apply_defaults(params))
        self.assertEqual(derived["PIPE_SIZE"], "4")
        self.assertAlmostEqual(derived["EDGE_SPACING_CM"], 5.08, places=6)
        self.assertAlmostEqual(derived["PIPE_OUTER_RADIUS_CM"], 5.715, places=3)
        self.assertAlmostEqual(derived["PIPE_PITCH_CM"], 16.51, places=2)

    def test_standard_nps_pipe_size_builds_successfully(self):
        """Test that array geometry can be generated from NPS sizing."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {
            "n_pipes": 2,
            "pipe_size": "3",
            "edge_spacing_cm": 2.54,
            "solution_radius_cm": None,
        }
        derived = template.derive_params(template.apply_defaults(params))
        all_params = {**template.apply_defaults(params), **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        self.assertEqual(dims["N_PIPES"], 2)
        self.assertAlmostEqual(dims["PIPE_OUTER_RADIUS_CM"], 4.445, places=3)
        self.assertAlmostEqual(dims["EDGE_SPACING_CM"], 2.54, places=6)
        self.assertGreater(len(geometry.root_universe.cells), 0)

    def test_with_water_moderator(self):
        """Test that water moderator is included when specified."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {"include_water": True}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        self.assertEqual(dims["INCLUDE_WATER"], True)

        # Check for water moderator cell
        cell_names = {cell.name for cell in geometry.root_universe.cells.values()}
        self.assertIn("water_moderator", cell_names)

    def test_without_water_moderator(self):
        """Test that water moderator can be excluded."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {"include_water": False}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        self.assertEqual(dims["INCLUDE_WATER"], False)

        # Check for void cell instead of water
        cell_names = {cell.name for cell in geometry.root_universe.cells.values()}
        self.assertIn("outside_void", cell_names)
        self.assertNotIn("water_moderator", cell_names)

    def test_reflective_boundaries(self):
        """Test that reflective boundaries simulate infinite array."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {"boundary_type": "reflective"}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        surfaces = geometry.get_all_surfaces()
        boundary_surfaces = [s for s in surfaces.values() if s.boundary_type == "reflective"]

        # Should have reflective boundaries
        self.assertGreaterEqual(len(boundary_surfaces), 4)  # At least x/y/z boundaries

    def test_vacuum_boundaries(self):
        """Test that vacuum boundaries create finite array."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {"boundary_type": "vacuum"}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)

        surfaces = geometry.get_all_surfaces()
        vacuum_surfaces = [s for s in surfaces.values() if s.boundary_type == "vacuum"]

        # Should have vacuum boundaries
        self.assertGreaterEqual(len(vacuum_surfaces), 4)

    def test_settings_creation(self):
        """Test that OpenMC settings are created correctly."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
        params = {}
        derived = template.derive_params(params)
        all_params = {**params, **derived, **template.get_simulation_params()}

        openmc.reset_auto_ids()
        materials, geometry, dims = model.build_model(all_params)
        settings = model.create_settings(all_params, dims)

        self.assertEqual(settings.run_mode, "eigenvalue")
        self.assertEqual(settings.particles, KCODE_SETTINGS["PARTICLES"])
        self.assertEqual(settings.batches, KCODE_SETTINGS["BATCHES"])
        self.assertEqual(settings.inactive, KCODE_SETTINGS["INACTIVE"])
        self.assertIsNotNone(settings.source)

    def test_plots_creation(self):
        """Test that geometry plots are created."""
        template = load_model_class("pipe-array")
        model = load_model_module(MODELS_ROOT / "pipe-array")
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
