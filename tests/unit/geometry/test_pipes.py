import unittest

from critbuddy.core.geometry.pipes import (
    PIPE_ALIASES,
    PIPE_REGISTRY,
    get_inner_radius,
    get_outer_radius,
    get_pipe,
    get_wall_thickness,
    list_pipes,
)


class PipeRegistryTests(unittest.TestCase):
    def test_get_pipe_returns_registry_spec(self):
        spec = get_pipe("2")

        self.assertEqual(spec.name, "2")
        self.assertEqual(spec.category, "cascade")
        self.assertIs(spec, PIPE_REGISTRY["2"])

    def test_get_pipe_resolves_aliases(self):
        self.assertEqual(PIPE_ALIASES["nps2"], "2")
        self.assertIs(get_pipe("nps2"), PIPE_REGISTRY["2"])

    def test_pipe_radius_and_thickness_helpers_match_registry_values(self):
        self.assertAlmostEqual(get_inner_radius("2"), 2.7395, places=6)
        self.assertAlmostEqual(get_outer_radius("2"), 3.016, places=6)
        self.assertAlmostEqual(get_wall_thickness("2"), 0.277, places=6)

    def test_list_pipes_filters_by_category(self):
        pigtails = dict(list_pipes(category="pigtail"))
        cascades = dict(list_pipes(category="cascade"))

        self.assertIn("1/4", pigtails)
        self.assertIn("2", cascades)
        self.assertNotIn("2", pigtails)

    def test_unknown_pipe_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_pipe("missing")


if __name__ == "__main__":
    unittest.main()
