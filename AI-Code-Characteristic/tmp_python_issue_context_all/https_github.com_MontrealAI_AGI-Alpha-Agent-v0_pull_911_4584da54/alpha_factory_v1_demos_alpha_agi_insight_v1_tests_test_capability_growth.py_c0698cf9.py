import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.simulation import forecast


def test_curve_helpers_expected_values() -> None:
    """Each curve helper should produce expected outputs."""
    assert forecast.linear_curve(-0.5) == 0.0
    assert forecast.linear_curve(0.5) == pytest.approx(0.5)
    assert forecast.linear_curve(2.0) == 1.0

    assert forecast.logistic_curve(0.0) == pytest.approx(0.5)
    assert 0.5 < forecast.logistic_curve(1.0) < 1.0

    assert forecast.exponential_curve(0.0) == pytest.approx(0.0)
    assert forecast.exponential_curve(1.0) == pytest.approx(1.0)


def test_capability_growth_dispatch() -> None:
    """Capability growth should dispatch to the appropriate curve."""
    t = 0.3
    assert forecast.capability_growth(t, curve="linear") == pytest.approx(forecast.linear_curve(t))
    assert forecast.capability_growth(t, curve="exponential") == pytest.approx(forecast.exponential_curve(t))
    assert forecast.capability_growth(t, curve="logistic") == pytest.approx(forecast.logistic_curve(10 * t))
    assert forecast.capability_growth(t) == pytest.approx(forecast.logistic_curve(10 * t))
