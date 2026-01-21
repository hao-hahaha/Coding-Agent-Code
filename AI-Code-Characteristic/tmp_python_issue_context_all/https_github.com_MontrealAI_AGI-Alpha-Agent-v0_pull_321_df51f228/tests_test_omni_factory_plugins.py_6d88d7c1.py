import unittest
from alpha_factory_v1.demos.omni_factory_demo import omni_factory_demo as demo

class TestPluginLoader(unittest.TestCase):
    def test_plugins_load_and_function(self):
        demo._load_plugins.cache_clear()
        plugins = demo._load_plugins()
        self.assertTrue(len(plugins) >= 1)
        plugin = plugins[0]
        heur = getattr(plugin, "heuristic_policy", None)
        self.assertTrue(callable(heur))
        result = heur([0.1, 0.5, 0.0])
        self.assertIn("action", result)

if __name__ == "__main__":
    unittest.main()
