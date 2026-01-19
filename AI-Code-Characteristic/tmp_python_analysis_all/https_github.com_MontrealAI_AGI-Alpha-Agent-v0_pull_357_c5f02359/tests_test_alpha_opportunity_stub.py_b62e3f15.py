import py_compile
import unittest
from pathlib import Path

STUB = Path('alpha_factory_v1/demos/aiga_meta_evolution/alpha_opportunity_stub.py')

class TestAlphaOpportunityStub(unittest.TestCase):
    def test_stub_compiles(self):
        py_compile.compile(STUB, doraise=True)

if __name__ == '__main__':
    unittest.main()
