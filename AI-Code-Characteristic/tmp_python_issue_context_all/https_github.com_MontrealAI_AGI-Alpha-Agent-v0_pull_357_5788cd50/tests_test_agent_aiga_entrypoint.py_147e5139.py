import py_compile
import unittest
from pathlib import Path

ENTRYPOINT = Path('alpha_factory_v1/demos/aiga_meta_evolution/agent_aiga_entrypoint.py')

class TestAgentAIGAEntry(unittest.TestCase):
    def test_entrypoint_compiles(self):
        py_compile.compile(ENTRYPOINT, doraise=True)

if __name__ == '__main__':
    unittest.main()
