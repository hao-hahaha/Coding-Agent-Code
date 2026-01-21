import py_compile
import unittest
from pathlib import Path

class TestOpenAIBridge(unittest.TestCase):
    def test_bridge_compiles(self):
        path = Path('alpha_factory_v1/demos/alpha_asi_world_model/openai_agents_bridge.py')
        py_compile.compile(path, doraise=True)

if __name__ == '__main__':
    unittest.main()
