import unittest

from alpha_factory_v1.demos.era_of_experience import alpha_detection


class TestAlphaDetection(unittest.TestCase):
    def test_detect_yield_curve_alpha(self) -> None:
        msg = alpha_detection.detect_yield_curve_alpha()
        self.assertIsInstance(msg, str)
        self.assertTrue("Yield curve spread" in msg)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
