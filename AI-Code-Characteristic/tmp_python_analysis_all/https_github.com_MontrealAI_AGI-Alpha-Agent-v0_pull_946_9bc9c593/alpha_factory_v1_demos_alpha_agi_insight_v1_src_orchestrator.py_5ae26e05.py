# SPDX-License-Identifier: Apache-2.0
"""Central process coordinating all Insight demo agents.

The orchestrator instantiates each agent, relays messages via the
:class:`~..utils.messaging.A2ABus` and restarts agents when they become
unresponsive. :meth:`run_forever` starts the event loop and periodic
health checks.
"""

from __future__ import annotations

import asyncio
import time
import contextlib
from typing import Callable, Dict, List

from .agents import (
    planning_agent,
    research_agent,
    strategy_agent,
    market_agent,
    codegen_agent,
    safety_agent,
    memory_agent,
)
from .utils import config, messaging, logging
from .utils.logging import Ledger
from .agents.base_agent import BaseAgent


class AgentRunner:
    """Wrapper supervising a single agent."""

    def __init__(self, agent: BaseAgent) -> None:
        self.cls: Callable[[messaging.A2ABus, Ledger], BaseAgent] = type(agent)
        self.agent: BaseAgent = agent
        self.period = getattr(agent, "CYCLE_SECONDS", 1.0)
        self.capabilities = getattr(agent, "CAPABILITIES", [])
        self.last_beat = time.time()
        self.task: asyncio.Task[None] | None = None

    async def loop(self, bus: messaging.A2ABus, ledger: Ledger) -> None:
        while True:
            try:
                await self.agent.run_cycle()
            except Exception as exc:  # noqa: BLE001
                logging._log.warning("%s failed: %s", self.agent.name, exc)
            env = messaging.Envelope(self.agent.name, "orch", {"heartbeat": True}, time.time())
            ledger.log(env)
            bus.publish("orch", env)
            self.last_beat = env.ts
            await asyncio.sleep(self.period)

    def start(self, bus: messaging.A2ABus, ledger: Ledger) -> None:
        self.task = asyncio.create_task(self.loop(bus, ledger))

    async def restart(self, bus: messaging.A2ABus, ledger: Ledger) -> None:
        if self.task:
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task
        self.agent = self.cls(bus, ledger)
        self.start(bus, ledger)


class Orchestrator:
    """Bootstraps agents and routes envelopes."""

    def __init__(self, settings: config.Settings | None = None) -> None:
        self.settings = settings or config.CFG
        logging.setup()
        self.bus = messaging.A2ABus(self.settings)
        self.ledger = Ledger(
            self.settings.ledger_path,
            rpc_url=self.settings.solana_rpc_url,
            wallet=self.settings.solana_wallet,
            broadcast=self.settings.broadcast,
        )
        self.runners: Dict[str, AgentRunner] = {}
        self.bus.subscribe("orch", self._on_orch)
        for agent in self._init_agents():
            runner = AgentRunner(agent)
            self.runners[agent.name] = runner
            self._register(runner)
        self._monitor_task: asyncio.Task[None] | None = None

    def _init_agents(self) -> List[BaseAgent]:
        agents = [
            planning_agent.PlanningAgent(self.bus, self.ledger),
            research_agent.ResearchAgent(self.bus, self.ledger),
            strategy_agent.StrategyAgent(self.bus, self.ledger),
            market_agent.MarketAgent(self.bus, self.ledger),
            codegen_agent.CodeGenAgent(self.bus, self.ledger),
            safety_agent.SafetyGuardianAgent(self.bus, self.ledger),
            memory_agent.MemoryAgent(self.bus, self.ledger, self.settings.memory_path),
        ]
        return agents

    def _register(self, runner: AgentRunner) -> None:
        env = messaging.Envelope(
            "orch",
            "system",
            {"event": "register", "agent": runner.agent.name, "capabilities": runner.capabilities},
            time.time(),
        )
        self.ledger.log(env)
        self.bus.publish("system", env)

    def _record_restart(self, runner: AgentRunner) -> None:
        env = messaging.Envelope(
            "orch",
            "system",
            {"event": "restart", "agent": runner.agent.name},
            time.time(),
        )
        self.ledger.log(env)
        self.bus.publish("system", env)

    async def _on_orch(self, env: messaging.Envelope) -> None:
        if env.payload.get("heartbeat") and env.sender in self.runners:
            self.runners[env.sender].last_beat = env.ts

    async def _monitor(self) -> None:
        while True:
            await asyncio.sleep(2)
            now = time.time()
            for r in list(self.runners.values()):
                if r.task and r.task.done():
                    await r.restart(self.bus, self.ledger)
                    self._record_restart(r)
                elif now - r.last_beat > r.period * 5:
                    logging._log.warning("%s unresponsive – restarting", r.agent.name)
                    await r.restart(self.bus, self.ledger)
                    self._record_restart(r)

    async def run_forever(self) -> None:
        await self.bus.start()
        self.ledger.start_merkle_task(3600)
        for r in self.runners.values():
            r.start(self.bus, self.ledger)
        self._monitor_task = asyncio.create_task(self._monitor())
        try:
            while True:
                await asyncio.sleep(0.5)
        finally:
            if self._monitor_task:
                self._monitor_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._monitor_task
            for r in self.runners.values():
                if r.task:
                    r.task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await r.task
            await self.bus.stop()
            await self.ledger.stop_merkle_task()
            self.ledger.close()


async def _main() -> None:  # pragma: no cover - CLI helper
    orch = Orchestrator()
    await orch.run_forever()


if __name__ == "__main__":  # pragma: no cover - CLI
    asyncio.run(_main())
