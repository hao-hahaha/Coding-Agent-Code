import py_compile
import unittest
from pathlib import Path

class TestGradioDashboard(unittest.TestCase):
    def test_dashboard_compiles(self) -> None:
        path = Path('alpha_factory_v1/demos/alpha_agi_business_v1/gradio_dashboard.py')
        py_compile.compile(path, doraise=True)

if __name__ == '__main__':
    unittest.main()
