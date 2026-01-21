from unittest import TestCase

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import forecast


class TestForecastFunctions(TestCase):
    def test_curve_helpers(self) -> None:
        self.assertEqual(forecast.linear_curve(-1.0), 0.0)
        self.assertEqual(forecast.linear_curve(2.0), 1.0)
        self.assertAlmostEqual(forecast.exponential_curve(0.0), 0.0)
        self.assertAlmostEqual(forecast.exponential_curve(1.0), 1.0)
        self.assertAlmostEqual(
            forecast.capability_growth(0.5, curve="linear"), 0.5
        )
        val = forecast.capability_growth(0.2, curve="exponential")
        self.assertGreaterEqual(val, 0.0)
        self.assertLessEqual(val, 1.0)

    def test_innovation_gain_positive(self) -> None:
        gain = forecast._innovation_gain(pop_size=2, generations=1)
        self.assertGreater(gain, 0.0)
        self.assertLess(gain, 0.1)
