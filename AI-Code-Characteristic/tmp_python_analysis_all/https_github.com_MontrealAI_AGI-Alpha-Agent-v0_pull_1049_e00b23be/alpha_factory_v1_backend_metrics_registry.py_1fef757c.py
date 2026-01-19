# SPDX-License-Identifier: Apache-2.0
"""Shared Prometheus metric registry."""

from __future__ import annotations

from typing import Any, Callable, MutableMapping

METRICS: MutableMapping[str, Any] = {}


def get_metric(factory: Callable[..., Any], name: str, desc: str, labels: list[str] | None = None) -> Any:
    """Return an existing metric or create a new one.

    This avoids depending on ``REGISTRY._names_to_collectors`` which may
    change between ``prometheus_client`` versions.
    """
    metric = METRICS.get(name)
    if metric is not None:
        return metric
    metric = factory(name, desc, labels) if labels is not None else factory(name, desc)
    METRICS[name] = metric
    return metric
