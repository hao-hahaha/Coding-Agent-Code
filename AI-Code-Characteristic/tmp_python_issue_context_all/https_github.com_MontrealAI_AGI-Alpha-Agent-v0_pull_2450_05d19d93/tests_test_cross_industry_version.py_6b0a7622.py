# SPDX-License-Identifier: Apache-2.0
"""Verify cross-industry demo exposes ``__version__``."""

import importlib
import unittest


class TestCrossIndustryVersion(unittest.TestCase):
    def test_has_version(self) -> None:
        mod = importlib.import_module("alpha_factory_v1.demos.cross_industry_alpha_factory")
        self.assertTrue(hasattr(mod, "__version__"))


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
