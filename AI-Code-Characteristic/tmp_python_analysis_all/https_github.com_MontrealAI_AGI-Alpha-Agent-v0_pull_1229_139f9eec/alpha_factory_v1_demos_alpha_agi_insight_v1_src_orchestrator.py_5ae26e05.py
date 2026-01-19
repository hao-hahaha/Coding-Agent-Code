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
import os
import random
from typing import Callable, Dict, List
from google.protobuf import struct_pb2

from .agents import (
    planning_agent,
    research_agent,
    strategy_agent,
    market_agent,
    codegen_agent,
    safety_agent,
    memory_agent,
    adk_summariser_agent,
)
from .utils import config, messaging, logging as insight_logging
from .utils.tracing import agent_cycle_seconds
from .utils import alerts
from .utils.logging import Ledger
from .agents.base_agent import BaseAgent
from src.governance.stake_registry import StakeRegistry

ERR_THRESHOLD = int(os.getenv("AGENT_ERR_THRESHOLD", "3"))
BACKOFF_EXP_AFTER = int(os.getenv("AGENT_BACKOFF_EXP_AFTER", "3"))
PROMOTION_THRESHOLD = float(os.getenv("PROMOTION_THRESHOLD", "0"))

log = insight_logging.logging.getLogger(__name__)


class AgentRunner:
    """Wrapper supervising a single agent."""

    def __init__(self, agent: BaseAgent) -> None:
        self.cls: Callable[[messaging.A2ABus, Ledger], BaseAgent] = type(agent)
        self.agent: BaseAgent = agent
        self.period = getattr(agent, "CYCLE_SECONDS", 1.0)
        self.capabilities = getattr(agent, "CAPABILITIES", [])
        self.last_beat = time.time()
        self.restarts = 0
        self.task: asyncio.Task[None] | None = None
        self.error_count = 0
        self.restart_streak = 0

    async def loop(self, bus: messaging.A2ABus, ledger: Ledger) -> None:
        while True:
            start = time.perf_counter()
            try:
                await self.agent.run_cycle()
            except Exception as exc:  # noqa: BLE001
                log.warning("%s failed: %s", self.agent.name, exc)
                alerts.send_alert(f"{self.agent.name} failed: {exc}")
                self.error_count += 1
            else:
                self.error_count = 0
                self.restart_streak = 0
                env = messaging.Envelope(
                    sender=self.agent.name,
                    recipient="orch",
                    payload=struct_pb2.Struct(),
                    ts=time.time(),
                )
                env.payload.update({"heartbeat": True})
                ledger.log(env)
                bus.publish("orch", env)
                self.last_beat = env.ts
            finally:
                agent_cycle_seconds.labels(self.agent.name).observe(time.perf_counter() - start)
            await asyncio.sleep(self.period)

    def start(self, bus: messaging.A2ABus, ledger: Ledger) -> None:
        self.task = asyncio.create_task(self.loop(bus, ledger))

    async def restart(self, bus: messaging.A2ABus, ledger: Ledger) -> None:
        if self.task:
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task
        try:
            close = getattr(self.agent, "close")
        except AttributeError:
            pass
        else:
            close()
        self.agent = self.cls(bus, ledger)
        self.error_count = 0
        self.restarts += 1
        self.restart_streak += 1
        self.start(bus, ledger)


class Orchestrator:
    """Bootstraps agents and routes envelopes."""

    def __init__(self, settings: config.Settings | None = None) -> None:
        self.settings = settings or config.CFG
        insight_logging.setup(json_logs=self.settings.json_logs)
        self.bus = messaging.A2ABus(self.settings)
        self.ledger = Ledger(
            self.settings.ledger_path,
            rpc_url=self.settings.solana_rpc_url,
            wallet=self.settings.solana_wallet,
            broadcast=self.settings.broadcast,
            db=self.settings.db_type,
        )
        self.registry = StakeRegistry()
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
            adk_summariser_agent.ADKSummariserAgent(self.bus, self.ledger),
            strategy_agent.StrategyAgent(self.bus, self.ledger),
            market_agent.MarketAgent(self.bus, self.ledger),
            codegen_agent.CodeGenAgent(self.bus, self.ledger),
            safety_agent.SafetyGuardianAgent(self.bus, self.ledger),
            memory_agent.MemoryAgent(self.bus, self.ledger, self.settings.memory_path),
        ]
        return agents

    def _register(self, runner: AgentRunner) -> None:
        env = messaging.Envelope(
            sender="orch",
            recipient="system",
            payload=struct_pb2.Struct(),
            ts=time.time(),
        )
        env.payload.update({"event": "register", "agent": runner.agent.name, "capabilities": runner.capabilities})
        self.ledger.log(env)
        self.bus.publish("system", env)
        self.registry.set_stake(runner.agent.name, 1.0)
        self.registry.set_threshold(f"promote:{runner.agent.name}", PROMOTION_THRESHOLD)

    def _record_restart(self, runner: AgentRunner) -> None:
        env = messaging.Envelope(
            sender="orch",
            recipient="system",
            payload=struct_pb2.Struct(),
            ts=time.time(),
        )
        env.payload.update({"event": "restart", "agent": runner.agent.name})
        self.ledger.log(env)
        self.bus.publish("system", env)
        alerts.send_alert(
            f"{runner.agent.name} restarted",
            self.settings.alert_webhook_url,
        )

    async def _on_orch(self, env: messaging.Envelope) -> None:
        if env.payload.get("heartbeat") and env.sender in self.runners:
            runner = self.runners[env.sender]
            runner.last_beat = env.ts
            runner.restart_streak = 0

    def slash(self, agent_id: str) -> None:
        """Burn 10% of ``agent_id`` stake."""
        self.registry.burn(agent_id, 0.1)

    def verify_merkle_root(self, expected: str, agent_id: str) -> None:
        """Slash ``agent_id`` when the ledger's Merkle root mismatches ``expected``."""
        actual = self.ledger.compute_merkle_root()
        if actual != expected:
            log.warning("Merkle mismatch for %s", agent_id)
            self.slash(agent_id)

    def verify_ledger(self, expected: str, agent_id: str) -> None:
        """Slash ``agent_id`` when the current ledger root mismatches ``expected``."""
        actual = self.ledger.compute_merkle_root()
        if actual != expected:
            log.warning("Merkle mismatch for %s", agent_id)
            self.slash(agent_id)

    async def _monitor(self) -> None:
        while True:
            await asyncio.sleep(2)
            now = time.time()
            for r in list(self.runners.values()):
                if r.task and r.task.done():
                    delay = random.uniform(0.5, 1.5)
                    if r.restart_streak >= BACKOFF_EXP_AFTER:
                        delay *= 2 ** (r.restart_streak - BACKOFF_EXP_AFTER + 1)
                    await asyncio.sleep(delay)
                    await r.restart(self.bus, self.ledger)
                    self._record_restart(r)
                elif r.error_count >= ERR_THRESHOLD:
                    log.warning("%s exceeded error threshold – restarting", r.agent.name)
                    delay = random.uniform(0.5, 1.5)
                    if r.restart_streak >= BACKOFF_EXP_AFTER:
                        delay *= 2 ** (r.restart_streak - BACKOFF_EXP_AFTER + 1)
                    await asyncio.sleep(delay)
                    await r.restart(self.bus, self.ledger)
                    self._record_restart(r)
                elif now - r.last_beat > r.period * 5:
                    log.warning("%s unresponsive – restarting", r.agent.name)
                    delay = random.uniform(0.5, 1.5)
                    if r.restart_streak >= BACKOFF_EXP_AFTER:
                        delay *= 2 ** (r.restart_streak - BACKOFF_EXP_AFTER + 1)
                    await asyncio.sleep(delay)
                    await r.restart(self.bus, self.ledger)
                    self._record_restart(r)

    async def run_forever(self) -> None:
        await self.bus.start()
        self.ledger.start_merkle_task(3600)
        for r in self.runners.values():
            proposal = f"promote:{r.agent.name}"
            if self.registry.accepted(proposal):
                r.start(self.bus, self.ledger)
            else:
                log.info("%s awaiting promotion", r.agent.name)
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
