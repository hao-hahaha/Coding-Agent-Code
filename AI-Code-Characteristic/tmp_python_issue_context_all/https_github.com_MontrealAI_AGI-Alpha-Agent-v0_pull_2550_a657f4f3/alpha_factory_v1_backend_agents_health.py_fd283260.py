# SPDX-License-Identifier: Apache-2.0
"""Background health monitoring for agents."""
from __future__ import annotations

import json
import threading
import time
from queue import Empty

from . import (
    _HEALTH_Q,
    _HEARTBEAT_INT,
    _RESCAN_SEC,
    AGENT_REGISTRY,
    _REGISTRY_LOCK,
    AgentMetadata,
    StubAgent,
    Counter,
    logger,
    _err_counter,
    _register,
    _emit_kafka,
    _ERR_THRESHOLD,
)
from .discovery import discover_hot_dir


def _health_loop() -> None:
    while True:
        try:
            name, latency_ms, ok = _HEALTH_Q.get(timeout=_HEARTBEAT_INT)
        except Empty:
            continue

        quarantine = False
        stub_meta: AgentMetadata | None = None
        with _REGISTRY_LOCK:
            meta = AGENT_REGISTRY.get(name)
            if meta and not ok:
                if Counter:
                    _err_counter.labels(agent=name).inc()  # type: ignore[attr-defined]
                object.__setattr__(meta, "err_count", meta.err_count + 1)
                if meta.err_count >= _ERR_THRESHOLD:  # type: ignore[name-defined]
                    logger.error(
                        "\N{NO ENTRY SIGN} Quarantining agent '%s' after %d consecutive errors",
                        name,
                        meta.err_count,
                    )
                    stub_meta = AgentMetadata(
                        name=meta.name,
                        cls=StubAgent,
                        version=meta.version + "+stub",
                        capabilities=meta.capabilities,
                        compliance_tags=meta.compliance_tags,
                    )
                    quarantine = True

        if quarantine and stub_meta:
            _register(stub_meta, overwrite=True)

        logger.debug(
            "heartbeat: %s ok=%s latency=%.1fms",
            name,
            ok,
            latency_ms,
        )
        _emit_kafka(  # type: ignore[name-defined]
            "agent.heartbeat",
            json.dumps({"name": name, "latency_ms": latency_ms, "ok": ok, "ts": time.time()}),
        )



def _rescan_loop() -> None:  # pragma: no cover
    while True:
        try:
            discover_hot_dir()
        except Exception:  # noqa: BLE001
            logger.exception("Hot-dir rescan failed")
        time.sleep(_RESCAN_SEC)


_bg_started = False
_health_thread: threading.Thread | None = None
_rescan_thread: threading.Thread | None = None


def start_background_tasks() -> None:
    """Launch health monitor and rescan loops exactly once."""
    global _bg_started, _health_thread, _rescan_thread
    if _bg_started:
        return
    _bg_started = True
    _health_thread = threading.Thread(target=_health_loop, daemon=True, name="agent-health")
    _rescan_thread = threading.Thread(target=_rescan_loop, daemon=True, name="agent-rescan")
    _health_thread.start()
    _rescan_thread.start()
