# SPDX-License-Identifier: Apache-2.0
"""Benchmark fitness calculation utilities."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping, Any

__all__ = ["compute_fitness"]


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
