import unittest
from unittest.mock import patch
import statistics

from alpha_factory_v1.backend.agents import finance_agent

class TestFinanceUtils(unittest.TestCase):
    def test_pct_basic(self):
        self.assertAlmostEqual(finance_agent._pct(100.0, 110.0), 0.1)
        self.assertEqual(finance_agent._pct(0.0, 5.0), 0.0)

    def test_cf_var_fallback(self):
        returns = [0.01, -0.02, 0.005, 0.015]
        mu = statistics.mean(returns)
        sig = statistics.pstdev(returns) or 1e-9
        expected = abs(mu + 2.326 * sig)
        with patch.object(finance_agent, "np", None, create=True), \
             patch.object(finance_agent, "skew", None, create=True), \
             patch.object(finance_agent, "kurtosis", None, create=True), \
             patch.object(finance_agent, "erfcinv", None, create=True):
            self.assertAlmostEqual(finance_agent._cf_var(returns), expected)

    def test_cvar(self):
        returns = [-0.1, 0.2, -0.05, 0.03]
        expected = 0.1
        self.assertAlmostEqual(finance_agent._cvar(returns), expected)

    def test_maxdd(self):
        returns = [0.1, -0.2, 0.05, -0.1]
        self.assertAlmostEqual(finance_agent._maxdd(returns), 0.244)

    def test_portfolio(self):
        p = finance_agent._Portfolio()
        p.update("BTC", 1.0)
        self.assertEqual(p.qty("BTC"), 1.0)
        self.assertEqual(p.book(), {"BTC": 1.0})
        self.assertEqual(p.value({"BTC": 100.0}), 100.0)
        p.update("BTC", -1.0)
        self.assertEqual(p.qty("BTC"), 0.0)
        self.assertEqual(p.book(), {})


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
