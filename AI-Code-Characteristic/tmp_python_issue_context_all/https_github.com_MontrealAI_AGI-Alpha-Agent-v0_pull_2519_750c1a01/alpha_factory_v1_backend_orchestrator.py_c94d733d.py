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
from typing import Dict

from alpha_factory_v1.utils.env import _env_int

from .telemetry import init_metrics, MET_LAT, MET_ERR, MET_UP, tracer  # noqa: F401
from .agent_manager import AgentManager
from .api_server import start_servers

with contextlib.suppress(ModuleNotFoundError):
    import uvicorn

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


async def _main() -> None:
    if os.getenv("NEO4J_PASSWORD") == "REPLACE_ME":
        log.error(
            "NEO4J_PASSWORD is set to the default 'REPLACE_ME'. "
            "Edit .env or your Docker secrets to configure a strong password."
        )
        sys.exit(1)

    mgr = AgentManager(ENABLED, DEV_MODE, KAFKA_BROKER, CYCLE_DEFAULT, MAX_CYCLE_SEC)
    log.info("Bootstrapped %d agent(s): %s", len(mgr.runners), ", ".join(mgr.runners))

    init_metrics(METRICS_PORT)

    rest_task, grpc_server = await start_servers(
        mgr.runners, MODEL_MAX_BYTES, mem, PORT, A2A_PORT, LOGLEVEL, SSL_DISABLE
    )

    stop_ev = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(RuntimeError):
            asyncio.get_running_loop().add_signal_handler(sig, stop_ev.set)

    await mgr.run(stop_ev)

    if rest_task:
        rest_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await rest_task
    if grpc_server:
        grpc_server.stop(0)
    log.info("Orchestrator shutdown complete")


class Orchestrator:
    """Programmatic entry-point wrapping :func:`_main`."""

    def run_forever(self) -> None:
        asyncio.run(_main())


if __name__ == "__main__":  # pragma: no cover - manual execution
    try:
        Orchestrator().run_forever()
    except KeyboardInterrupt:
        pass
