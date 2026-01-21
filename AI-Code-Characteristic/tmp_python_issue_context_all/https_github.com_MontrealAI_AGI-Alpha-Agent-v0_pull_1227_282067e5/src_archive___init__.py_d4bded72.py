# SPDX-License-Identifier: Apache-2.0
"""Simple SQLite archive for agent metadata and scores."""
from __future__ import annotations

import json
import math
import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from src.monitoring import metrics

from .db import ArchiveDB, ArchiveEntry


@dataclass(slots=True)
class Agent:
    """Archive entry."""

    id: int
    meta: dict[str, Any]
    score: float


class Archive:
    """Persist agent records and provide weighted sampling."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._ensure()

    def _ensure(self) -> None:
        with sqlite3.connect(self.path) as cx:
            cx.execute(
                "CREATE TABLE IF NOT EXISTS agents("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "meta TEXT,"
                "score REAL"
                ")"
            )

    def _update_metrics(self) -> None:
        records = self.all()
        if not records:
            return
        scores = [a.score for a in records]
        metrics.dgm_best_score.set(max(scores))
        metrics.dgm_archive_mean.set(sum(scores) / len(scores))
        metrics.dgm_lineage_depth.set(len(records))

    def add(self, meta: dict[str, Any], score: float) -> None:
        with sqlite3.connect(self.path) as cx:
            cx.execute("INSERT INTO agents(meta, score) VALUES (?, ?)", (json.dumps(meta), score))
        self._update_metrics()

    def all(self) -> List[Agent]:
        with sqlite3.connect(self.path) as cx:
            rows = list(cx.execute("SELECT id, meta, score FROM agents ORDER BY id"))
        return [Agent(id=r[0], meta=json.loads(r[1]), score=float(r[2])) for r in rows]

    def sample(self, k: int, *, lam: float = 10.0, alpha0: float = 0.5) -> List[Agent]:
        agents = self.all()
        if not agents:
            return []
        weights = [1.0 / (1.0 + math.exp(-lam * (a.score - alpha0))) for a in agents]
        chosen = random.choices(agents, weights=weights, k=min(k, len(agents)))
        return chosen


__all__ = ["Agent", "Archive", "ArchiveDB", "ArchiveEntry"]
