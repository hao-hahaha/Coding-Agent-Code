# SPDX-License-Identifier: Apache-2.0
"""Capsule facts loader and impact scoring utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping

import yaml


@dataclass(slots=True)
class CapsuleFacts:
    """Minimal capsule fact bundle."""

    market_size: float
    efficiency_gain: float
    llm_score: float | None = None


def load_capsule_facts(base: str | Path | None = None) -> MutableMapping[str, CapsuleFacts]:
    """Return mapping of sector name to :class:`CapsuleFacts`."""

    base_path = Path(base or Path(__file__).parent)
    facts: MutableMapping[str, CapsuleFacts] = {}
    for entry in base_path.iterdir():
        if not entry.is_dir():
            continue
        yaml_path = entry / "facts.yml"
        if not yaml_path.exists():
            continue
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        facts[entry.name] = CapsuleFacts(
            market_size=float(data.get("market_size", 0.0)),
            efficiency_gain=float(data.get("efficiency_gain", 0.0)),
            llm_score=(float(data.get("llm_score")) if data.get("llm_score") is not None else None),
        )
    return facts


class ImpactScorer:
    """Compute impact scores from capsule facts."""

    def __init__(self, llm_weight: float = 0.5) -> None:
        self.llm_weight = llm_weight

    def score(self, facts: CapsuleFacts, efficiency_gain: float) -> float:
        """Return the impact score."""
        base = facts.market_size * efficiency_gain
        if facts.llm_score is not None:
            base *= 1.0 + self.llm_weight * facts.llm_score
        return base


__all__ = ["CapsuleFacts", "load_capsule_facts", "ImpactScorer"]
