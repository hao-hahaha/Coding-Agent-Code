# SPDX-License-Identifier: Apache-2.0
"""Prometheus metrics exporter wrapper."""

from __future__ import annotations

from ..telemetry import init_metrics


class MetricsExporter:
    """Thin wrapper around :func:`init_metrics`."""

    def __init__(self, port: int) -> None:
        self._port = port

    def start(self) -> None:
        init_metrics(self._port)

    def stop(self) -> None:  # pragma: no cover - no teardown required
        return None
