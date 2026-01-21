# SPDX-License-Identifier: Apache-2.0
"""Metrics and tracing helpers for the orchestrator."""

from __future__ import annotations

import contextlib
import logging
from typing import Any, Callable, List

# Optional dependencies
with contextlib.suppress(ModuleNotFoundError):
    from opentelemetry import trace

with contextlib.suppress(ModuleNotFoundError):
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        CONTENT_TYPE_LATEST,
        generate_latest,
        start_http_server,
    )

log = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__) if "trace" in globals() else None  # type: ignore


def _noop_metric(*_a: Any, **_kw: Any) -> Any:
    class _Metric:  # pylint: disable=too-few-public-methods
        def labels(self, *_a: Any, **_kw: Any) -> "_Metric":
            return self

        def observe(self, *_a: Any) -> None:
            ...

        def inc(self, *_a: Any) -> None:
            ...

        def set(self, *_a: Any) -> None:
            ...

    return _Metric()


if "Histogram" in globals():
    from alpha_factory_v1.backend.metrics_registry import get_metric as _reg_metric

    def _get_metric(factory: Callable[..., Any], name: str, desc: str, labels: list[str] | None = None) -> Any:
        return _reg_metric(factory, name, desc, labels)

    MET_LAT = _get_metric(Histogram, "af_agent_cycle_latency_ms", "Per-cycle latency", ["agent"])
    MET_ERR = _get_metric(Counter, "af_agent_cycle_errors_total", "Exceptions per agent", ["agent"])
    MET_UP = _get_metric(Gauge, "af_agent_up", "1 = agent alive according to HB", ["agent"])
else:  # pragma: no cover - metrics optional
    MET_LAT = _noop_metric()
    MET_ERR = _noop_metric()
    MET_UP = _noop_metric()

# Exported symbols for mypy
__all__: List[str] = [
    "tracer",
    "MET_LAT",
    "MET_ERR",
    "MET_UP",
    "init_metrics",
]
if "generate_latest" in globals():
    __all__.extend(["generate_latest", "CONTENT_TYPE_LATEST"])


def init_metrics(port: int) -> None:
    """Start the Prometheus exporter if possible."""

    if port and "start_http_server" in globals():
        start_http_server(port)
        log.info("Prometheus metrics exposed at :%d/metrics", port)
