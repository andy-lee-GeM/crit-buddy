import tempfile
import textwrap
import unittest
import importlib.util
from pathlib import Path

from critbuddy.models.model_interface import OMCModel

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_LOADER_PATH = ROOT / "critbuddy" / "core" / "template_loader.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


template_loader = _load_module(TEMPLATE_LOADER_PATH, "test_template_loader")
load_openmc_model = template_loader.load_openmc_model


class OpenMCModelLoaderTests(unittest.TestCase):
    def _write_model(self, root: Path, source: str) -> Path:
        model_dir = root / "demo-model" / "openmc"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "model.py").write_text(textwrap.dedent(source), encoding="utf-8")
        return model_dir.parent

    def test_load_openmc_model_returns_concrete_class_instance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_root = self._write_model(
                Path(tmpdir),
                """
                from critbuddy.models.model_interface import OMCModel

                class DemoModel(OMCModel):
                    def create_materials(self, params):
                        return ("materials",)

                    def build_model(self, params):
                        return ("materials", "geometry", {"demo": True})

                    def create_settings(self, params, dims):
                        return "settings"

                    def create_plots(self, dims, materials):
                        return ("plots", {"Fuel": "red"})
                """,
            )

            model = load_openmc_model(model_root)

            self.assertIsInstance(model, OMCModel)
            self.assertEqual(model.__class__.__name__, "DemoModel")
            self.assertEqual(model.build_model({}), ("materials", "geometry", {"demo": True}))

    def test_load_openmc_model_raises_for_multiple_candidates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_root = self._write_model(
                Path(tmpdir),
                """
                from critbuddy.models.model_interface import OMCModel

                class First(OMCModel):
                    def create_materials(self, params):
                        return ()
                    def build_model(self, params):
                        return (None, None, {})
                    def create_settings(self, params, dims):
                        return None
                    def create_plots(self, dims, materials):
                        return (None, {})

                class Second(OMCModel):
                    def create_materials(self, params):
                        return ()
                    def build_model(self, params):
                        return (None, None, {})
                    def create_settings(self, params, dims):
                        return None
                    def create_plots(self, dims, materials):
                        return (None, {})
                """,
            )

            with self.assertRaisesRegex(ValueError, "Multiple OMCModel implementations found"):
                load_openmc_model(model_root)

    def test_load_openmc_model_uses_legacy_fallback_temporarily(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            model_root = self._write_model(
                Path(tmpdir),
                """
                def build_model(params):
                    return ("materials", "geometry", {"legacy": True})

                def create_settings(params, dims):
                    return "settings"

                def create_plots(dims, materials):
                    return ("plots", {"Fuel": "red"})
                """,
            )

            model = load_openmc_model(model_root)

            self.assertIsInstance(model, OMCModel)
            self.assertEqual(model.build_model({}), ("materials", "geometry", {"legacy": True}))


if __name__ == "__main__":
    unittest.main()
