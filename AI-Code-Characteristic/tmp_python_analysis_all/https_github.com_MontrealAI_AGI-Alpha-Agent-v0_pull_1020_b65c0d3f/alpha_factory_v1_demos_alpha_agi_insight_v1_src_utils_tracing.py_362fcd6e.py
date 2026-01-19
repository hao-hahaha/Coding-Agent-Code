# SPDX-License-Identifier: Apache-2.0
"""OpenTelemetry helpers used by the Insight demo."""
from __future__ import annotations

import os
from contextlib import nullcontext
from typing import Any, ContextManager, cast

metrics: Any | None
trace: Any | None

try:  # optional dependency
    from opentelemetry import metrics as otel_metrics, trace as otel_trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.metrics.export import OTLPMetricExporter  # type: ignore[attr-defined]
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.trace.export import OTLPSpanExporter  # type: ignore[attr-defined]
    metrics = otel_metrics
    trace = otel_trace
except Exception:  # pragma: no cover - missing SDK
    metrics = None
    trace = None

__all__ = ["tracer", "meter", "span", "configure"]

tracer = None
meter = None


def configure() -> None:
    """Initialise tracing and metrics if the SDK is installed."""
    global tracer, meter
    if trace is None or metrics is None:
        return

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        span_exporter = OTLPSpanExporter(endpoint=endpoint)
        metric_exporter = OTLPMetricExporter(endpoint=endpoint)
    else:
        span_exporter = ConsoleSpanExporter()
        metric_exporter = ConsoleMetricExporter()

    resource = Resource.create({"service.name": "alpha-insight"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("alpha_insight")

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PeriodicExportingMetricReader(metric_exporter)],
    )
    metrics.set_meter_provider(meter_provider)
    meter = metrics.get_meter("alpha_insight")


def span(name: str) -> ContextManager[Any]:
    """Return a context manager for ``name``."""
    if tracer:
        return cast(ContextManager[Any], tracer.start_as_current_span(name))
    return nullcontext()


configure()
