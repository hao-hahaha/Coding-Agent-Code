import unittest
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HELM_DIR = ROOT / "helm"

class HelmChartTests(unittest.TestCase):
    def check_chart_file(self, chart_path: Path):
        self.assertTrue(chart_path.is_file(), f"{chart_path} missing")
        text = chart_path.read_text()
        for key in ["apiVersion:", "name:", "version:", "appVersion:"]:
            self.assertIn(key, text, f"{key} not found in {chart_path}")

    def test_alpha_factory_chart(self):
        chart = HELM_DIR / "alpha-factory" / "Chart.yaml"
        values = HELM_DIR / "alpha-factory" / "values.yaml"
        self.check_chart_file(chart)
        self.assertTrue(values.is_file(), "values.yaml missing for alpha-factory")

    def test_alpha_factory_remote_chart(self):
        chart = HELM_DIR / "alpha-factory-remote" / "Chart.yaml"
        values = HELM_DIR / "alpha-factory-remote" / "values.yaml"
        helpers = HELM_DIR / "alpha-factory-remote" / "templates" / "_helpers.tpl"
        self.check_chart_file(chart)
        self.assertTrue(values.is_file(), "values.yaml missing for alpha-factory-remote")
        self.assertTrue(helpers.is_file(), "_helpers.tpl missing for alpha-factory-remote")

if __name__ == "__main__":
    unittest.main()
