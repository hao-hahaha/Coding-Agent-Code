from __future__ import annotations

from src.critics import DualCriticService
from src.analysis.chaos_monkey import ChaosMonkey


def test_adversarial_cases_detected() -> None:
    service = DualCriticService(["The sky is blue."])
    monkey = ChaosMonkey(service)
    fraction = monkey.detected_fraction("The sky is blue.", "The sky is blue.")
    assert fraction >= 0.8
