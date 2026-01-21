from alpha_factory_v1.demos.alpha_agi_insight_v1.src.evaluators import lead_time


def test_lead_signal_improvement_over_baseline() -> None:
    history = [1.0, 1.0, 1.0]
    forecast = [1.2, 1.3, 1.4]
    score = lead_time.lead_signal_improvement(history, forecast, months=3, threshold=1.1)
    assert score >= 0.15

