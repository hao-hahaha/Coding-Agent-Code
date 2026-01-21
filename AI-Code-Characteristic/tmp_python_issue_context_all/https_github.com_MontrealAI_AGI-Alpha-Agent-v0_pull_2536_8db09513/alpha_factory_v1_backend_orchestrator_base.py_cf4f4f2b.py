# SPDX-License-Identifier: Apache-2.0
"""Common orchestrator utilities used across demos."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Optional

from .agent_manager import AgentManager
from .api_server import start_servers


class BaseOrchestrator:
    """Simple helper managing an :class:`AgentManager` and optional servers."""

    def __init__(
        self,
        enabled: set[str],
        dev_mode: bool,
        kafka_broker: str | None,
        cycle_seconds: int,
        max_cycle_sec: int,
        *,
        rest_port: int,
        grpc_port: int,
        model_max_bytes: int,
        mem: object,
        loglevel: str,
        ssl_disable: bool,
        manager: AgentManager | None = None,
    ) -> None:
        self.manager = manager or AgentManager(enabled, dev_mode, kafka_broker, cycle_seconds, max_cycle_sec)
        self._rest_port = rest_port
        self._grpc_port = grpc_port
        self._model_max_bytes = model_max_bytes
        self._mem = mem
        self._loglevel = loglevel
        self._ssl_disable = ssl_disable
        self._rest_task: Optional[asyncio.Task[None]] = None
        self._grpc_server: Optional[object] = None

    async def start(self) -> None:
        """Launch REST and gRPC servers and background tasks."""
        self._rest_task, self._grpc_server = await start_servers(
            self.manager.runners,
            self._model_max_bytes,
            self._mem,
            self._rest_port,
            self._grpc_port,
            self._loglevel,
            self._ssl_disable,
        )
        await self.manager.start()

    async def stop(self) -> None:
        """Stop servers and agent manager."""
        await self.manager.stop()
        if self._rest_task:
            self._rest_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._rest_task
        if self._grpc_server:
            self._grpc_server.stop(0)

    async def run(self, stop_event: asyncio.Event) -> None:
        """Run until ``stop_event`` is set."""
        await self.start()
        await self.manager.run(stop_event)
        await self.stop()

    def run_forever(self) -> None:
        """Convenience wrapper used by scripts."""
        asyncio.run(self.run(asyncio.Event()))
