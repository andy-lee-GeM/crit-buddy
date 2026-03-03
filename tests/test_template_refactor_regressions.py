import unittest
from pathlib import Path

import openmc

from critbuddy.core.template_loader import load_template_class, load_template_module


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


class TemplateRefactorRegressionTests(unittest.TestCase):
    def _build(self, template_name: str, user_params: dict):
        template = load_template_class(template_name)
        params = template.apply_defaults(user_params)
        errors = template.validate_params(params)
        self.assertEqual(errors, [], f"Validation errors for {template_name}: {errors}")
        derived = template.derive_params(params)

        module = load_template_module(TEMPLATES / template_name)
        openmc.reset_auto_ids()
        materials, geometry, dims = module.build_model(derived)
        return derived, materials, geometry, dims

    def test_shipping_template_has_fissile_z_keys(self):
        template = load_template_class("shipping_cylinder")
        params = template.apply_defaults(
            {
                "enrichment": 5.0,
                "cylinder_type": "30b",
            }
        )
        errors = template.validate_params(params)
        self.assertEqual(errors, [])
        derived = template.derive_params(params)

        self.assertIn("Z_FISSILE_BOTTOM", derived)
        self.assertIn("Z_FISSILE_TOP", derived)

    def test_shipping_uo2f2_is_respected(self):
        _, materials, _, _ = self._build(
            "shipping_cylinder",
            {
                "enrichment": 5.0,
                "cylinder_type": "30b",
                "fissile_material": "uo2f2",
                "h_to_u": 20.0,
            },
        )
        names = {m.name for m in materials}
        self.assertTrue(any(name.startswith("UO2F2") for name in names))
        self.assertNotIn("UF6", names)

    def test_rectangular_box_uo2f2_is_respected(self):
        _, materials, _, _ = self._build(
            "rectangular_box",
            {
                "enrichment": 5.0,
                "fissile_material": "uo2f2",
                "h_to_u": 25.0,
                "length_cm": 20.0,
                "width_cm": 20.0,
                "height_cm": 20.0,
            },
        )
        names = {m.name for m in materials}
        self.assertTrue(any(name.startswith("UO2F2") for name in names))
        self.assertNotIn("UF6", names)

    def test_environment_material_and_density_propagate(self):
        derived, _, _, _ = self._build(
            "cylinder",
            {
                "enrichment": 5.0,
                "radius_cm": 5.0,
                "height_cm": 20.0,
                "environment_material": "air",
                "environment_density": 0.0014,
            },
        )
        self.assertEqual(derived["ENVIRONMENT_MATERIAL"], "air")
        self.assertAlmostEqual(derived["ENV_DENSITY"], 0.0014, places=6)

    def test_legacy_environment_alias_is_rejected(self):
        template = load_template_class("pipe")
        params = template.apply_defaults(
            {
                "enrichment": 5.0,
                "pipe_size": "2",
                "length_cm": 100.0,
                "environment": "water",
            }
        )
        errors = template.validate_params(params)
        self.assertTrue(any("Unknown parameter 'environment'" in e for e in errors))

    def test_cascade_array_uses_gap_xy_and_gap_z(self):
        template = load_template_class("cascade_array")
        params = template.apply_defaults(
            {
                "enrichment": 5.0,
                "R_inner_cm": 5.0,
                "H_inner_cm": 50.0,
                "t_wall_cm": 0.3,
                "wall_material": "steel",
                "i": 2,
                "j": 3,
                "k": 2,
                "gap_xy_cm": 1.25,
                "gap_z_cm": 3.5,
            }
        )
        errors = template.validate_params(params)
        self.assertEqual(errors, [])

        d = template.derive_params(params)
        gap_xy = params["gap_xy_cm"]
        gap_z = params["gap_z_cm"]

        self.assertAlmostEqual(d["GAP_XY"], gap_xy, places=6)
        self.assertAlmostEqual(d["GAP_Z"], gap_z, places=6)
        self.assertAlmostEqual(d["PITCH_CYLINDER"] - 2.0 * d["R_OUTER"], gap_xy, places=6)
        self.assertAlmostEqual(d["PITCH_Z"] - d["H_OUTER"], gap_z, places=6)
        self.assertAlmostEqual(d["ARRAY_X"], d["CASSETTE_X"], places=6)
        self.assertAlmostEqual(d["ARRAY_Y"], d["CASSETTE_Y"], places=6)
        self.assertAlmostEqual(d["ARRAY_Z"], d["CASSETTE_Z"], places=6)

    def test_cascade_array_rejects_gap_cm_alias(self):
        template = load_template_class("cascade_array")
        params = template.apply_defaults(
            {
                "enrichment": 5.0,
                "R_inner_cm": 5.0,
                "H_inner_cm": 50.0,
                "i": 1,
                "j": 1,
                "k": 1,
                "gap_cm": 1.25,
            }
        )
        errors = template.validate_params(params)
        self.assertTrue(any("Unknown parameter 'gap_cm'" in e for e in errors))

    def test_cascade_array_placement_generator_matches_config(self):
        template = load_template_class("cascade_array")
        params = template.apply_defaults(
            {
                "enrichment": 20.0,
                "R_inner_cm": 12.7,
                "H_inner_cm": 101.5,
                "t_wall_cm": 0.3175,
                "wall_material": "aluminum",
                "i": 2,
                "j": 5,
                "k": 5,
                "gap_xy_cm": 6.0,
                "gap_z_cm": 100.0,
            }
        )
        errors = template.validate_params(params)
        self.assertEqual(errors, [])
        d = template.derive_params(params)

        module = load_template_module(TEMPLATES / "cascade_array")
        placements = list(module.iter_cylinder_placements(d))

        self.assertEqual(len(placements), d["TOTAL_CYLINDERS"])

        xs = [p.x_center for p in placements]
        ys = [p.y_center for p in placements]
        zs = [p.z_base for p in placements]

        self.assertAlmostEqual(min(xs), d["R_OUTER"], places=6)
        self.assertAlmostEqual(min(ys), d["R_OUTER"], places=6)
        self.assertAlmostEqual(min(zs), 0.0, places=6)

        expected_x_max = d["R_OUTER"] + (d["I"] - 1) * d["PITCH_CYLINDER"]
        expected_y_max = d["R_OUTER"] + (d["J"] - 1) * d["PITCH_CYLINDER"]
        expected_z_max = (d["K"] - 1) * d["PITCH_Z"]

        self.assertAlmostEqual(max(xs), expected_x_max, places=6)
        self.assertAlmostEqual(max(ys), expected_y_max, places=6)
        self.assertAlmostEqual(max(zs), expected_z_max, places=6)

    def test_cascade_array_split_gaps_and_reflective_boundary(self):
        derived, materials, geometry, dims = self._build(
            "cascade_array",
            {
                "enrichment": 20.0,
                "R_inner_cm": 12.7,
                "H_inner_cm": 101.5,
                "t_wall_cm": 0.3175,
                "wall_material": "aluminum",
                "i": 2,
                "j": 5,
                "k": 5,
                "gap_xy_cm": 6.0,
                "gap_z_cm": 100.0,
                "boundary_type": "reflective",
            },
        )

        self.assertAlmostEqual(derived["GAP_XY"], 6.0, places=6)
        self.assertAlmostEqual(derived["GAP_Z"], 100.0, places=6)
        self.assertAlmostEqual(derived["PITCH_CYLINDER"] - 2.0 * derived["R_OUTER"], 6.0, places=6)
        self.assertAlmostEqual(derived["PITCH_Z"] - derived["H_OUTER"], 100.0, places=6)

        # Reflective mode uses half-gap boundary pads and no explicit water shell.
        self.assertEqual(dims["BOUNDARY_TYPE"], "reflective")
        self.assertAlmostEqual(dims["TOTAL_X"], derived["ARRAY_X"] + derived["GAP_XY"], places=6)
        self.assertAlmostEqual(dims["TOTAL_Y"], derived["ARRAY_Y"] + derived["GAP_XY"], places=6)
        self.assertAlmostEqual(dims["TOTAL_Z"], derived["ARRAY_Z"] + derived["GAP_Z"], places=6)

        cell_names = {c.name for c in geometry.root_universe.cells.values()}
        self.assertNotIn("reflector", cell_names)

        material_names = {m.name for m in materials}
        self.assertFalse(any(name.startswith("Water") for name in material_names))

        surfaces = geometry.get_all_surfaces()
        named_surfaces = {s.name: s for s in surfaces.values()}
        for plane_name in ("x_min", "x_max", "y_min", "y_max", "z_min", "z_max"):
            self.assertIn(plane_name, named_surfaces)
            self.assertEqual(named_surfaces[plane_name].boundary_type, "reflective")

    def test_cascade_array_vacuum_uses_environment_shell_not_water(self):
        _, materials, geometry, dims = self._build(
            "cascade_array",
            {
                "enrichment": 5.0,
                "R_inner_cm": 5.0,
                "H_inner_cm": 50.0,
                "i": 1,
                "j": 1,
                "k": 1,
                "gap_xy_cm": 5.0,
                "gap_z_cm": 10.0,
                "boundary_type": "vacuum",
            },
        )

        self.assertEqual(dims["BOUNDARY_TYPE"], "vacuum")
        cell_names = {c.name for c in geometry.root_universe.cells.values()}
        self.assertIn("environment_shell", cell_names)
        self.assertNotIn("reflector", cell_names)

        material_names = {m.name for m in materials}
        self.assertFalse(any(name.startswith("Water") for name in material_names))


if __name__ == "__main__":
    unittest.main()
