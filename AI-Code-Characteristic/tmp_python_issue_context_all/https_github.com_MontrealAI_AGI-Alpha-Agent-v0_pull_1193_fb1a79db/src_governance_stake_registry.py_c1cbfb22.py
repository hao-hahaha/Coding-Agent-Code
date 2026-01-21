# SPDX-License-Identifier: Apache-2.0
"""Simple stake registry supporting stake-weighted voting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, MutableMapping


@dataclass
class StakeRegistry:
    """In-memory stake and vote tracking."""

    stakes: MutableMapping[str, float] = field(default_factory=dict)
    votes: Dict[str, Dict[str, bool]] = field(default_factory=dict)

    def set_stake(self, agent_id: str, amount: float) -> None:
        """Register ``agent_id`` with ``amount`` tokens."""
        self.stakes[agent_id] = float(amount)

    def burn(self, agent_id: str, fraction: float) -> None:
        """Burn ``fraction`` of ``agent_id``'s stake if present."""
        if agent_id in self.stakes:
            self.stakes[agent_id] = max(0.0, self.stakes[agent_id] * (1.0 - fraction))

    def total(self) -> float:
        """Return total stake across all agents."""
        return float(sum(self.stakes.values()))

    def vote(self, proposal_id: str, agent_id: str, support: bool) -> None:
        """Record ``agent_id``'s vote for ``proposal_id``."""
        if agent_id not in self.stakes:
            raise ValueError(f"unknown agent {agent_id}")
        self.votes.setdefault(proposal_id, {})[agent_id] = bool(support)

    def accepted(self, proposal_id: str) -> bool:
        """Return ``True`` iff yes votes reach two-thirds of total stake."""
        total = self.total()
        if total == 0:
            return False
        votes = self.votes.get(proposal_id, {})
        yes = sum(self.stakes[a] for a, v in votes.items() if v)
        return yes / total >= 2 / 3
