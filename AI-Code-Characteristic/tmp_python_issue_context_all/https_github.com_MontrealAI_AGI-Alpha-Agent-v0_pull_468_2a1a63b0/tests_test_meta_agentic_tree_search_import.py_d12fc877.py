import importlib
import unittest

class TestMetaAgenticTreeSearchImport(unittest.TestCase):
    """Verify package-level exports for the MATS demo."""

    def test_package_exports(self) -> None:
        mod = importlib.import_module("alpha_factory_v1.demos.meta_agentic_tree_search_v0")
        self.assertTrue(hasattr(mod, "run_demo"))
        self.assertTrue(hasattr(mod, "mats"))
        self.assertTrue(hasattr(mod, "openai_agents_bridge"))

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
