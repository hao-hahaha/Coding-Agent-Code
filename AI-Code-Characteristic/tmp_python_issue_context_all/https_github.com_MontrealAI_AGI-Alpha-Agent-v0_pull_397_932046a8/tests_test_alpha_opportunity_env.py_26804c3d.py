import json
import os
import unittest
from pathlib import Path

from alpha_factory_v1.demos.alpha_agi_business_v1 import alpha_agi_business_v1 as biz

class TestAlphaOpportunityEnv(unittest.TestCase):
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

if __name__ == "__main__":  # pragma: no cover
    unittest.main()
