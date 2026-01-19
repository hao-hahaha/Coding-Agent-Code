# SPDX-License-Identifier: Apache-2.0
"""Analyse orchestrator logs and propose refinement patches."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Mapping

from src.governance.stake_registry import StakeRegistry
from src.self_evolution import harness
from src.tools.diff_mutation import propose_diff
from src.tools import test_scribe

__all__ = ["MetaRefinementAgent"]


class MetaRefinementAgent:
    """Generate diff proposals based on orchestrator log analysis."""

    def __init__(self, repo: str | Path, log_dir: str | Path, registry: StakeRegistry | None = None) -> None:
        self.repo = Path(repo)
        self.log_dir = Path(log_dir)
        self.registry = registry or StakeRegistry()
        if "meta" not in self.registry.stakes:
            self.registry.set_stake("meta", 1.0)

    # ------------------------------------------------------------------
    def _load_logs(self) -> List[Mapping[str, object]]:
        records: List[Mapping[str, object]] = []
        for file in sorted(self.log_dir.glob("*.json")):
            for line in file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    @staticmethod
    def _detect_bottleneck(entries: Iterable[Mapping[str, object]]) -> str | None:
        prev_ts: float | None = None
        max_delta = -1.0
        target: str | None = None
        for rec in entries:
            ts = float(rec.get("ts", 0.0))
            if prev_ts is not None:
                delta = ts - prev_ts
                if delta > max_delta:
                    max_delta = delta
                    target = str(rec.get("hash", ""))
            prev_ts = ts
        return target

    def _create_patch(self, bottleneck: str) -> str:
        goal = f"optimise around {bottleneck}"
        metric = self.repo / "metric.txt"
        if metric.exists():
            try:
                current = int(float(metric.read_text().strip()))
            except Exception:
                current = 0
            new_val = current + 1
            diff = "--- a/metric.txt\n" "+++ b/metric.txt\n" "@@\n" f"-{current}\n" f"+{new_val}\n"
            return diff
        return propose_diff(str(metric), goal)

    # ------------------------------------------------------------------
    def refine(self) -> bool:
        """Generate and apply a patch addressing the detected bottleneck.

        Returns:
            bool: ``True`` if the patch was merged, ``False`` otherwise.
        """
        logs = self._load_logs()
        bottleneck = self._detect_bottleneck(logs)
        if not bottleneck:
            return False
        diff = self._create_patch(bottleneck)
        accepted = harness.vote_and_merge(self.repo, diff, self.registry, agent_id="meta")
        if accepted:
            test_scribe.generate_test(self.repo, "True")
        return accepted
