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

    def test_aiga_bridge_compiles(self):
        """Ensure the AI-GA demo bridge compiles."""
        path = Path('alpha_factory_v1/demos/aiga_meta_evolution/openai_agents_bridge.py')
        py_compile.compile(path, doraise=True)

    def test_cross_industry_bridge_compiles(self):
        """Ensure the cross-industry demo bridge compiles."""
        path = Path('alpha_factory_v1/demos/cross_industry_alpha_factory/openai_agents_bridge.py')
        py_compile.compile(path, doraise=True)

    def test_mats_bridge_compiles(self):
        """Ensure the MATS demo bridge compiles."""
        path = Path('alpha_factory_v1/demos/meta_agentic_tree_search_v0/openai_agents_bridge.py')
        py_compile.compile(path, doraise=True)

    def test_insight_bridge_compiles(self):
        """Ensure the α‑AGI Insight demo bridge compiles."""
        path = Path('alpha_factory_v1/demos/alpha_agi_insight_v0/openai_agents_bridge.py')
        py_compile.compile(path, doraise=True)

if __name__ == '__main__':
    unittest.main()
