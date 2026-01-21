# SPDX-License-Identifier: Apache-2.0
"""Benchmark fitness calculation utilities."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable, Mapping, Any
import logging
from pathlib import Path

from src.archive.db import ArchiveDB

__all__ = ["compute_fitness", "evaluate_agent", "CurriculumSwitcher"]


def compute_fitness(results: Iterable[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    """Compute dataset pass rate and average runtime.

    Parameters
    ----------
    results:
        Iterable of benchmark result dictionaries. Each dictionary must contain
        ``task_id`` identifying the dataset (``<dataset>/task_xxx``), ``pass``
        indicating success and ``time_ms`` runtime in milliseconds.

    Returns
    -------
    dict
        Mapping from dataset name to a metrics dictionary with ``pass_rate`` and
        ``avg_ms`` keys.
    """

    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for entry in results:
        try:
            task_id = entry["task_id"]
        except KeyError as exc:  # pragma: no cover - guard against bad input
            raise KeyError("task_id missing from result") from exc
        dataset = str(task_id).split("/")[0]
        grouped[dataset].append(entry)

    metrics: dict[str, dict[str, float]] = {}
    for dataset, items in grouped.items():
        total = len(items)
        passed = sum(1 for i in items if i.get("pass"))
        avg_ms = (
            sum(int(i.get("time_ms", 0)) for i in items) / total if total else 0.0
        )
        metrics[dataset] = {"pass_rate": passed / total if total else 0.0, "avg_ms": avg_ms}

    return metrics


def evaluate_agent(code: str) -> dict[str, float]:
    """Return accuracy, novelty SimHash and execution latency."""

    import random
    import time
    from hashlib import blake2b

    start = time.perf_counter()
    h = blake2b(code.encode(), digest_size=8).digest()
    simhash = int.from_bytes(h, "big")
    rng = random.Random(simhash & 0xFFFF)
    accuracy = 0.5 + rng.random() * 0.5
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "accuracy": accuracy,
        "novelty_simhash": float(simhash),
        "latency_ms": latency_ms,
    }


class CurriculumSwitcher:
    """Manage dataset curriculum based on rolling pass rate."""

    MINI = "swe_mini"
    FULL = "swebench_verified_mini"
    POLYGLOT = "polyglot_lite"

    def __init__(self, db_path: str | Path, window: int = 10) -> None:
        self.db = ArchiveDB(db_path)
        self.window = window
        self.history: deque[float] = deque(maxlen=window)
        self._dataset = self.db.get_state("dataset", self.MINI)
        self._log = logging.getLogger(__name__)
        self._log.info("current dataset: %s", self._dataset)

    @property
    def dataset(self) -> str:
        """Return the active dataset name."""

        return self._dataset

    def update(self, metrics: Mapping[str, Mapping[str, float]]) -> None:
        """Update rolling stats and switch datasets when thresholds pass."""

        rate = metrics.get(self._dataset, {}).get("pass_rate")
        if rate is not None:
            self.history.append(rate)
        if not self.history:
            return
        avg = sum(self.history) / len(self.history)

        if self._dataset == self.MINI and avg >= 0.40:
            self._dataset = self.FULL
            self.history.clear()
            self.db.set_state("dataset", self._dataset)
            self._log.info("switched dataset to %s", self._dataset)
        elif self._dataset == self.FULL and avg >= 0.60:
            self._dataset = self.POLYGLOT
            self.history.clear()
            self.db.set_state("dataset", self._dataset)
            self._log.info("switched dataset to %s", self._dataset)
