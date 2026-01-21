import json
import unittest
from pathlib import Path

class TestBusinessNotebook(unittest.TestCase):
    def test_notebook_valid(self) -> None:
        nb_path = Path("alpha_factory_v1/demos/alpha_agi_business_v1/colab_alpha_agi_business_v1_demo.ipynb")
        self.assertTrue(nb_path.exists(), "Notebook missing")
        data = json.loads(nb_path.read_text(encoding="utf-8"))
        self.assertIn("cells", data)
        self.assertIn("nbformat", data)
        self.assertGreaterEqual(data.get("nbformat", 0), 4)

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
