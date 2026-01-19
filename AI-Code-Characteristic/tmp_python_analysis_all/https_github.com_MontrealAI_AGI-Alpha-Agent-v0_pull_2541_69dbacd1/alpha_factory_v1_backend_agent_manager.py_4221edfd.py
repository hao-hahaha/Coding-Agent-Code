# SPDX-License-Identifier: Apache-2.0
"""Agent scheduling and heartbeat management."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Dict, Optional

from .agent_runner import AgentRunner, EventBus, hb_watch, regression_guard


class AgentManager:
    """Manage a collection of :class:`AgentRunner` instances."""

    def __init__(
        self,
        enabled: set[str],
        dev_mode: bool,
        kafka_broker: str | None,
        cycle_seconds: int,
        max_cycle_sec: int,
        *,
        bus: EventBus | None = None,
    ) -> None:
        from backend.agents import list_agents, start_background_tasks

        start_background_tasks()
        avail = list_agents()
        names = [n for n in avail if not enabled or n in enabled]
        if not names:
            raise RuntimeError(f"No agents selected – ENABLED={','.join(enabled) if enabled else 'ALL'}")

        self.bus = bus or EventBus(kafka_broker, dev_mode)
        self.runners: Dict[str, AgentRunner] = {
            n: AgentRunner(n, cycle_seconds, max_cycle_sec, self.bus.publish) for n in names
        }
        self._hb_task: Optional[asyncio.Task] = None
        self._reg_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Launch heartbeat and regression guard tasks."""

        self._hb_task = asyncio.create_task(hb_watch(self.runners))
        self._reg_task = asyncio.create_task(regression_guard(self.runners))

    async def stop(self) -> None:
        """Cancel helper tasks and wait for agent cycles to finish."""

        if self._hb_task:
            self._hb_task.cancel()
        if self._reg_task:
            self._reg_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            if self._hb_task:
                await self._hb_task
            if self._reg_task:
                await self._reg_task
        await asyncio.gather(*(r.task for r in self.runners.values() if r.task), return_exceptions=True)

    async def run(self, stop_event: asyncio.Event) -> None:
        """Drive all runners until *stop_event* is set."""

        await self.start()
        try:
            while not stop_event.is_set():
                await asyncio.gather(*(r.maybe_step() for r in self.runners.values()))
                await asyncio.sleep(0.25)
        finally:
            await self.stop()


__all__ = ["AgentManager"]
