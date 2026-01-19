# SPDX-License-Identifier: Apache-2.0
"""OpenTelemetry helpers used by the Insight demo."""
from __future__ import annotations

import os
from contextlib import nullcontext

try:  # optional dependency
    from opentelemetry import metrics, trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        OTLPMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        OTLPSpanExporter,
    )
except Exception:  # pragma: no cover - missing SDK
    metrics = trace = None  # type: ignore

__all__ = ["tracer", "meter", "span", "configure"]

tracer = None
meter = None


def configure() -> None:
    """Initialise tracing and metrics if the SDK is installed."""
    global tracer, meter
    if trace is None:
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


def span(name: str):
    """Return a context manager for ``name``."""
    if tracer:
        return tracer.start_as_current_span(name)
    return nullcontext()


configure()
