# SPDX-License-Identifier: Apache-2.0
"""Unit tests for alpha_report.best_alpha."""

import unittest

from alpha_factory_v1.demos.era_of_experience import alpha_report


class TestBestAlpha(unittest.TestCase):
    """Ensure heuristics pick the expected message."""

    def test_selects_supply_chain_bottleneck(self) -> None:
        signals = {
            "yield_curve": "yield curve normal",
            "supply_chain": "flows 12m usd – POTENTIAL BOTTLENECK",
        }
        self.assertEqual(alpha_report.best_alpha(signals), signals["supply_chain"])

    def test_selects_long_bonds(self) -> None:
        signals = {
            "yield_curve": "spread -0.5, consider LONG BONDS soon",
            "supply_chain": "all clear",
        }
        self.assertEqual(alpha_report.best_alpha(signals), signals["yield_curve"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
