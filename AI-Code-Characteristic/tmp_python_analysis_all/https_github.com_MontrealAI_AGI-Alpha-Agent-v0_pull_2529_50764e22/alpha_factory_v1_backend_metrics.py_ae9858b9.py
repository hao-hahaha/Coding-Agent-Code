# SPDX-License-Identifier: Apache-2.0
"""Prometheus metrics helpers."""

from __future__ import annotations

from .telemetry import (
    init_metrics as _init_metrics,
    MET_LAT,
    MET_ERR,
    MET_UP,
    tracer,
)

__all__ = ["init_metrics", "MET_LAT", "MET_ERR", "MET_UP", "tracer"]


def init_metrics(port: int) -> None:
    """Initialise metric exporter."""
    _init_metrics(port)
