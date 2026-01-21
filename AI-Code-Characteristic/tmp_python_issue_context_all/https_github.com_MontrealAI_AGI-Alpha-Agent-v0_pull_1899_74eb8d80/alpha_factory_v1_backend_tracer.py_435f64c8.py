# SPDX-License-Identifier: Apache-2.0
"""alpha_factory_v1.backend.tracer
=================================

Lightweight tracer used by the agents and planner to persist execution spans.

Design goals
------------
* **Minimal API.** A single :class:`Tracer` instance offers both synchronous
  and asynchronous helpers.
* **Production ready.** Calls never raise; failures are logged and skipped.
* **Opt‑in observability.** Tracing can be disabled via ``AF_TRACING=false``.

Usage example
-------------
>>> mem = Memory()
>>> tracer = Tracer(mem)
>>> with tracer.span("demo", "think"):
...     expensive_call()
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import logging
import os
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, asdict
from typing import Any, Generator

log = logging.getLogger("Tracer")


@dataclass(slots=True)
class Span:
    """Structured trace payload."""

    ts: str
    phase: str
    payload: Any


class Tracer:
    """Capture and persist execution spans."""

    def __init__(self, memory: Any, *, enabled: bool | None = None) -> None:
        """Create a tracer backed by ``memory``.

        Args:
            memory: Object exposing a ``write`` method used to persist spans.
            enabled: Override the ``AF_TRACING`` environment variable if set.
        """
        self.mem = memory
        if enabled is None:
            enabled = os.getenv("AF_TRACING", "true").lower() != "false"
        self.enabled = enabled

    # ------------------------------------------------------------------ sync
    def record(self, agent_name: str, phase: str, payload: Any) -> None:
        """Persist one tracing span."""
        if not self.enabled:
            return
        span = Span(
            ts=_dt.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            phase=phase,
            payload=payload,
        )
        try:
            self.mem.write(agent_name, f"trace:{phase}", asdict(span))
        except Exception as exc:  # pragma: no cover - defensive
            log.error("Trace write failed: %s", exc)
        else:
            log.debug("Trace %s %s", agent_name, phase)

    # ---------------------------------------------------------------- async
    async def arecord(self, agent_name: str, phase: str, payload: Any) -> None:
        """Async wrapper around :meth:`record`."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.record, agent_name, phase, payload)

    # ---------------------------------------------------------------- context
    @contextmanager
    def span(self, agent_name: str, phase: str, **payload: Any) -> Generator[None, None, None]:
        """Context manager that records duration in ``payload['duration_ms']``."""
        start = _dt.datetime.utcnow()
        try:
            yield
        finally:
            duration = (_dt.datetime.utcnow() - start).total_seconds() * 1000
            payload["duration_ms"] = round(duration, 3)
            self.record(agent_name, phase, payload)

    @asynccontextmanager
    async def aspan(self, agent_name: str, phase: str, **payload: Any) -> Generator[None, None, None]:
        """Async variant of :meth:`span`."""
        start = _dt.datetime.utcnow()
        try:
            yield
        finally:
            duration = (_dt.datetime.utcnow() - start).total_seconds() * 1000
            payload["duration_ms"] = round(duration, 3)
            await self.arecord(agent_name, phase, payload)


__all__ = ["Tracer", "Span"]

