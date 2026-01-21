import unittest
import importlib

class TestAgentsAlias(unittest.TestCase):
    def test_backend_alias(self):
        a = importlib.import_module("alpha_factory_v1.backend.agents")
        b = importlib.import_module("backend.agents")
        self.assertIs(a, b)

if __name__ == "__main__":
    unittest.main()
