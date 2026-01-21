import json
import unittest
from pathlib import Path

class TestMetaAgenticNotebook(unittest.TestCase):
    """Validate the meta_agentic_agi demo notebook."""

    def test_notebook_valid(self) -> None:
        nb_path = Path("alpha_factory_v1/demos/meta_agentic_agi/colab_meta_agentic_agi.ipynb")
        self.assertTrue(nb_path.exists(), "Notebook missing")
        data = json.loads(nb_path.read_text(encoding="utf-8"))
        self.assertIn("cells", data)
        self.assertIn("nbformat", data)
        self.assertGreaterEqual(data.get("nbformat", 0), 4)

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
