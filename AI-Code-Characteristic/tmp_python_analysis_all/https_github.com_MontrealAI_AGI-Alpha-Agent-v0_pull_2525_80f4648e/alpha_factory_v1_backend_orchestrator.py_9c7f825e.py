# SPDX-License-Identifier: Apache-2.0
# This code is a conceptual research prototype.
"""Alpha‑Factory orchestrator wrapper."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import signal
import sys


from alpha_factory_v1.utils.env import _env_int

from .telemetry import init_metrics, MET_LAT, MET_ERR, MET_UP, tracer  # noqa: F401
from .orchestrator_base import BaseOrchestrator

with contextlib.suppress(ModuleNotFoundError):
    import uvicorn  # noqa: F401

# Memory fabric is optional → graceful stub when absent
try:
    from backend.memory_fabric import mem
except ModuleNotFoundError:  # pragma: no cover
    from typing import Any, List

    class _VecDummy:  # pylint: disable=too-few-public-methods
        def recent(self, *_a: Any, **_kw: Any) -> List[Any]:
            return []

        def search(self, *_a: Any, **_kw: Any) -> List[Any]:
            return []

    class _MemStub:  # pylint: disable=too-few-public-methods
        vector = _VecDummy()

    mem = _MemStub()


ENV = os.getenv

DEV_MODE = ENV("DEV_MODE", "false").lower() == "true" or "--dev" in sys.argv
LOGLEVEL = ENV("LOGLEVEL", "INFO").upper()
PORT = _env_int("PORT", 8000)
METRICS_PORT = _env_int("METRICS_PORT", 0)
A2A_PORT = _env_int("A2A_PORT", 0)
SSL_DISABLE = ENV("INSECURE_DISABLE_TLS", "false").lower() == "true"
KAFKA_BROKER = None if DEV_MODE else ENV("ALPHA_KAFKA_BROKER")
CYCLE_DEFAULT = _env_int("ALPHA_CYCLE_SECONDS", 60)
MAX_CYCLE_SEC = _env_int("MAX_CYCLE_SEC", 30)
MODEL_MAX_BYTES = _env_int("ALPHA_MODEL_MAX_BYTES", 64 * 1024 * 1024)
ENABLED = {s.strip() for s in ENV("ALPHA_ENABLED_AGENTS", "").split(",") if s.strip()}

if not logging.getLogger().handlers:
    logging.basicConfig(
        level=LOGLEVEL,
        format="%(asctime)s.%(msecs)03d %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
log = logging.getLogger("alpha_factory.orchestrator")

_manager: BaseOrchestrator | None = None


def _publish(topic: str, msg: dict[str, object]) -> None:
    """Expose bus.publish for agent modules."""
    if _manager is not None:
        try:
            _manager.manager.bus.publish(topic, msg)
        except Exception:  # pragma: no cover - best effort
            log.exception("publish failed")


class Orchestrator(BaseOrchestrator):
    """Default Alpha‑Factory orchestrator."""

    def __init__(self) -> None:
        if os.getenv("NEO4J_PASSWORD") == "REPLACE_ME":
            log.error(
                "NEO4J_PASSWORD is set to the default 'REPLACE_ME'. "
                "Edit .env or your Docker secrets to configure a strong password."
            )
            sys.exit(1)

        init_metrics(METRICS_PORT)

        super().__init__(
            ENABLED,
            DEV_MODE,
            KAFKA_BROKER,
            CYCLE_DEFAULT,
            MAX_CYCLE_SEC,
            rest_port=PORT,
            grpc_port=A2A_PORT,
            model_max_bytes=MODEL_MAX_BYTES,
            mem=mem,
            loglevel=LOGLEVEL,
            ssl_disable=SSL_DISABLE,
        )

        global _manager
        _manager = self

        log.info(
            "Bootstrapped %d agent(s): %s",
            len(self.manager.runners),
            ", ".join(self.manager.runners),
        )

    def run_forever(self) -> None:
        """Run the orchestrator with signal handling."""
        stop_ev = asyncio.Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            with contextlib.suppress(RuntimeError):
                asyncio.get_running_loop().add_signal_handler(sig, stop_ev.set)

        try:
            asyncio.run(self.run(stop_ev))
        finally:
            log.info("Orchestrator shutdown complete")


if __name__ == "__main__":  # pragma: no cover - manual execution
    try:
        Orchestrator().run_forever()
    except KeyboardInterrupt:
        pass
