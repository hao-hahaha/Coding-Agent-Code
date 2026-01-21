# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from src.capsules import CapsuleFacts, load_capsule_facts, ImpactScorer


def test_load_capsule_facts(tmp_path: Path) -> None:
    d = tmp_path / "health"
    d.mkdir()
    (d / "facts.yml").write_text(
        """\
market_size: 10
efficiency_gain: 0.2
llm_score: 0.5
""",
        encoding="utf-8",
    )

    facts = load_capsule_facts(tmp_path)
    assert "health" in facts
    f = facts["health"]
    assert f.market_size == 10
    assert f.efficiency_gain == 0.2
    assert f.llm_score == 0.5


def test_impact_score() -> None:
    facts = CapsuleFacts(market_size=100, efficiency_gain=0.1, llm_score=0.6)
    scorer = ImpactScorer(llm_weight=0.5)
    score = scorer.score(facts, 0.2)
    assert score == 100 * 0.2 * (1 + 0.5 * 0.6)
