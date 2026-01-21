import json
import unittest
from pathlib import Path

class TestMetaAgenticNotebook(unittest.TestCase):
    """Validate the shipped meta-agentic demo notebooks."""

    def _check_notebook(self, path: Path) -> None:
        self.assertTrue(path.exists(), f"Notebook missing: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("cells", data)
        self.assertIn("nbformat", data)
        self.assertGreaterEqual(data.get("nbformat", 0), 4)

    def test_notebook_v1_valid(self) -> None:
        self._check_notebook(Path("alpha_factory_v1/demos/meta_agentic_agi/colab_meta_agentic_agi.ipynb"))

    def test_notebook_v2_valid(self) -> None:
        self._check_notebook(Path("alpha_factory_v1/demos/meta_agentic_agi_v2/colab_meta_agentic_agi_v2.ipynb"))

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
