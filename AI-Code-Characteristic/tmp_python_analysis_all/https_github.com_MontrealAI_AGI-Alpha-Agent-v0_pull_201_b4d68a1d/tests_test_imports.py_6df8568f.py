import importlib
import unittest


class TestImports(unittest.TestCase):
    """Verify that the package can be imported."""

    def test_alpha_factory_import(self) -> None:
        mod = importlib.import_module("alpha_factory_v1")
        self.assertTrue(hasattr(mod, "__version__"))


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()

