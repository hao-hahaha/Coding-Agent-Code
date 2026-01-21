import py_compile
import unittest
from pathlib import Path

class TestOpenAIBridge(unittest.TestCase):
    def test_asi_bridge_compiles(self):
        """Ensure the ASI demo bridge compiles."""
        path = Path('alpha_factory_v1/demos/alpha_asi_world_model/openai_agents_bridge.py')
        py_compile.compile(path, doraise=True)

    def test_meta_bridge_compiles(self):
        """Ensure the meta-agentic demo bridge compiles."""
        path = Path('alpha_factory_v1/demos/meta_agentic_agi/openai_agents_bridge.py')
        py_compile.compile(path, doraise=True)

    def test_business_bridge_compiles(self):
        """Ensure the business demo bridge compiles."""
        path = Path('alpha_factory_v1/demos/alpha_agi_business_v1/openai_agents_bridge.py')
        py_compile.compile(path, doraise=True)

if __name__ == '__main__':
    unittest.main()
