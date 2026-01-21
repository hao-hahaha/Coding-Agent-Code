import py_compile
import unittest
from pathlib import Path

AGENT = Path('alpha_factory_v1/backend/agents/aiga_evolver_agent.py')

class TestAIGAEvolverAgent(unittest.TestCase):
    def test_agent_compiles(self) -> None:
        py_compile.compile(AGENT, doraise=True)

if __name__ == '__main__':
    unittest.main()
