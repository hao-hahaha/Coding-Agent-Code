# SPDX-License-Identifier: Apache-2.0
import unittest

from alpha_factory_v1.backend import alpha_model as am

class AlphaModelTest(unittest.TestCase):
    def test_momentum(self):
        prices = [1, 2, 3, 4, 5]
        self.assertAlmostEqual(am.momentum(prices, lookback=4), 4.0)
        self.assertEqual(am.momentum(prices, lookback=10), 0.0)

    def test_sma_crossover(self):
        prices = [5, 4, 3, 2, 3, 4]
        self.assertEqual(am.sma_crossover(prices, fast=2, slow=4), 1)
        prices = [2, 3, 4, 5, 4, 3]
        self.assertEqual(am.sma_crossover(prices, fast=2, slow=4), -1)

    def test_ema(self):
        prices = [1] * 5 + [10]
        self.assertGreater(am.ema(prices, span=3), 1)

    def test_rsi(self):
        uptrend = list(range(1, 20))
        self.assertGreater(am.rsi(uptrend, period=5), 70)
        downtrend = list(range(20, 1, -1))
        self.assertLess(am.rsi(downtrend, period=5), 30)

    def test_bollinger_bands(self):
        prices = [1, 2, 3, 4, 5]
        lower, upper = am.bollinger_bands(prices, window=4, num_std=1)
        self.assertLess(lower, upper)

    def test_invalid_params_raise(self):
        with self.assertRaises(ValueError):
            am.momentum([1, 2], lookback=0)
        with self.assertRaises(ValueError):
            am.sma_crossover([1]*5, fast=0, slow=1)
        with self.assertRaises(ValueError):
            am.sma_crossover([1]*5, fast=5, slow=3)
        with self.assertRaises(ValueError):
            am.ema([1], span=0)
        with self.assertRaises(ValueError):
            am.rsi([1, 2], period=0)
        with self.assertRaises(ValueError):
            am.bollinger_bands([1], window=0)


if __name__ == "__main__":
    unittest.main()
