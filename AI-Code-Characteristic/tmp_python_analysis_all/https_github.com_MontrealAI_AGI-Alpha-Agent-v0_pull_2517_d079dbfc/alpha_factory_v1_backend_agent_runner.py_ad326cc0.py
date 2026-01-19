# SPDX-License-Identifier: Apache-2.0
# This code is a conceptual research prototype.
"""Agent scheduling and health monitoring utilities."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
import atexit
from datetime import datetime, timezone
from collections import deque
from typing import Any, Dict, Optional, Callable

from backend.agents import get_agent
from src.monitoring import metrics

from .telemetry import MET_LAT, MET_ERR, MET_UP, tracer

with contextlib.suppress(ModuleNotFoundError):
    from kafka import KafkaProducer

log = logging.getLogger(__name__)


class EventBus:
    """Simple Kafka/in-memory event bus."""

    def __init__(self, broker: str | None, dev_mode: bool) -> None:
        self._queues: Dict[str, asyncio.Queue] | None = None
        self._producer: KafkaProducer | None = None  # type: ignore
        if broker and "KafkaProducer" in globals():
            self._producer = KafkaProducer(
                bootstrap_servers=broker.split(","),
                value_serializer=lambda v: json.dumps(v).encode(),
                linger_ms=50,
            )
            atexit.register(self._close)
        else:
            if broker and not dev_mode:
                log.warning("Kafka unavailable → falling back to in-proc bus")
            self._queues = {}

    def publish(self, topic: str, msg: Dict[str, Any]) -> None:
        if self._producer:
            self._producer.send(topic, msg)
        else:
            assert self._queues is not None
            self._queues.setdefault(topic, asyncio.Queue()).put_nowait(msg)

    def _close(self) -> None:
        if not self._producer:
            return
        try:
            self._producer.flush()
            self._producer.close()
        except Exception:  # noqa: BLE001
            log.exception("Kafka producer close failed")


async def maybe_await(fn, *a, **kw):  # type: ignore
    return await fn(*a, **kw) if asyncio.iscoroutinefunction(fn) else await asyncio.to_thread(fn, *a, **kw)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class AgentRunner:
    """Wrap one agent instance and manage its execution."""

    def __init__(
        self,
        name: str,
        cycle_seconds: int,
        max_cycle_sec: int,
        publish: callable,
        inst: object | None = None,
    ) -> None:
        self.name = name
        self.inst = inst or get_agent(name)
        self.period = getattr(self.inst, "CYCLE_SECONDS", cycle_seconds)
        self.spec = getattr(self.inst, "SCHED_SPEC", None)
        self.next_ts = 0.0
        self.last_beat = time.time()
        self.task: Optional[asyncio.Task] = None
        self._max_cycle_sec = max_cycle_sec
        self._publish = publish
        self._calc_next()

        with contextlib.suppress(ModuleNotFoundError):
            from openai.agents import AgentContext  # type: ignore[attr-defined]

            if isinstance(self.inst, AgentContext):
                from .telemetry import tracer  # avoid circular import
                from openai.agents import AgentRuntime  # type: ignore[attr-defined]

                runtime = AgentRuntime()
                runtime.register(self.inst)
                atexit.register(runtime.close)

    def _calc_next(self) -> None:
        now = time.time()
        if self.spec:
            with contextlib.suppress(ModuleNotFoundError, ValueError):
                from croniter import croniter  # type: ignore

                self.next_ts = croniter(self.spec, datetime.fromtimestamp(now)).get_next(float)
                return
        self.next_ts = now + self.period

    async def maybe_step(self) -> None:
        if time.time() < self.next_ts:
            return
        self._calc_next()

        async def _cycle() -> None:
            t0 = time.time()
            span_cm = tracer.start_as_current_span(self.name) if tracer else contextlib.nullcontext()
            with span_cm:
                try:
                    await asyncio.wait_for(maybe_await(self.inst.run_cycle), timeout=self._max_cycle_sec)
                except asyncio.TimeoutError:
                    MET_ERR.labels(self.name).inc()
                    log.error("%s run_cycle exceeded %ss budget – skipped", self.name, self._max_cycle_sec)
                except Exception as exc:  # noqa: BLE001
                    MET_ERR.labels(self.name).inc()
                    log.exception("%s.run_cycle crashed: %s", self.name, exc)
                finally:
                    dur_ms = (time.time() - t0) * 1_000
                    MET_LAT.labels(self.name).observe(dur_ms)
                    self.last_beat = time.time()
                    self._publish("agent.cycle", {"agent": self.name, "latency_ms": dur_ms, "ts": utc_now()})

        self.task = asyncio.create_task(_cycle())


async def hb_watch(runners: Dict[str, AgentRunner]) -> None:
    while True:
        now = time.time()
        for n, r in runners.items():
            alive = int(now - r.last_beat < r.period * 3.0)
            MET_UP.labels(n).set(alive)
        await asyncio.sleep(5)


async def regression_guard(runners: Dict[str, AgentRunner], on_alert: Callable[[str], None] | None = None) -> None:
    history: deque[float] = deque(maxlen=3)
    while True:
        await asyncio.sleep(1)
        try:
            sample = metrics.dgm_best_score.collect()[0].samples[0]
            score = float(sample.value)
        except Exception:  # pragma: no cover - metrics optional
            continue
        history.append(score)
        if len(history) == 3 and history[1] <= history[0] * 0.8 and history[2] <= history[1] * 0.8:
            runner = runners.get("aiga_evolver")
            if runner and runner.task:
                runner.task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await runner.task
            if on_alert:
                on_alert("Evolution paused due to metric regression")
            history.clear()
