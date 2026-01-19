import json
import os
import unittest
from pathlib import Path

from alpha_factory_v1.demos.alpha_agi_business_v1 import alpha_agi_business_v1 as biz


class TestAlphaOpportunityEnv(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_files: list[Path] = []
        self.env_vars: dict[str, str] = {}

    def tearDown(self) -> None:
        for p in self.temp_files:
            try:
                Path(p).unlink()
            except FileNotFoundError:
                pass
        for var in self.env_vars:
            os.environ.pop(var, None)

    def test_env_override(self):
        data = [{"alpha": "env test"}]
        tmp = Path("/tmp/opps.json")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.environ["ALPHA_OPPS_FILE"] = str(tmp)
        try:
            agent = biz.AlphaOpportunityAgent()
            self.assertEqual(agent._opportunities, data)
        finally:
            del os.environ["ALPHA_OPPS_FILE"]
            tmp.unlink()

    def test_best_only_sorting(self):
        data = [
            {"alpha": "low", "score": 1},
            {"alpha": "high", "score": 5}
        ]
        tmp = Path("/tmp/opps2.json")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        self.temp_files.append(tmp)
        os.environ["ALPHA_OPPS_FILE"] = str(tmp)
        os.environ["ALPHA_BEST_ONLY"] = "1"
        self.env_vars["ALPHA_OPPS_FILE"] = str(tmp)
        self.env_vars["ALPHA_BEST_ONLY"] = "1"
        agent = biz.AlphaOpportunityAgent()
        self.assertEqual(agent._opportunities[0]["alpha"], "high")

    def test_top_n(self):
        data = [
            {"alpha": "low", "score": 1},
            {"alpha": "mid", "score": 3},
            {"alpha": "high", "score": 5},
        ]
        tmp = Path("/tmp/opps3.json")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        self.temp_files.append(tmp)
        self.set_env_var("ALPHA_OPPS_FILE", str(tmp))
        self.set_env_var("ALPHA_TOP_N", "2")
        agent = biz.AlphaOpportunityAgent()
        self.assertEqual(agent._top_n, 2)
        self.assertEqual(agent._opportunities[0]["alpha"], "high")
        self.assertEqual(agent._opportunities[1]["alpha"], "mid")

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
