import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import asyncio
import contextlib
from unittest import mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src import orchestrator
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.base_agent import BaseAgent


class BoomAgent(BaseAgent):
    """Agent that fails on the first cycle."""

    CYCLE_SECONDS = 0.1

    def __init__(self, bus: orchestrator.messaging.A2ABus, ledger: orchestrator.Ledger) -> None:  # type: ignore[override]
        super().__init__("boom", bus, ledger)
        self.first = True

    async def run_cycle(self) -> None:
        if self.first:
            self.first = False
            raise RuntimeError("boom")
        await asyncio.sleep(0)

    async def handle(self, _env: orchestrator.messaging.Envelope) -> None:  # pragma: no cover - helper
        pass


def test_restart_crashed_agent(monkeypatch: mock.Mock) -> None:
    events: list[str | None] = []

    class DummyLedger:
        def __init__(self, *_a, **_kw) -> None:
            pass

        def log(self, env) -> None:  # type: ignore[override]
            events.append(env.payload.get("event"))

        def start_merkle_task(self, *_a, **_kw) -> None:
            pass

        async def stop_merkle_task(self) -> None:
            pass

        def close(self) -> None:
            pass

    settings = config.Settings(bus_port=0)
    monkeypatch.setattr(orchestrator, "Ledger", DummyLedger)
    monkeypatch.setattr(
        orchestrator.Orchestrator, "_init_agents", lambda self: [BoomAgent(self.bus, self.ledger)]
    )

    async def loop_no_catch(self: orchestrator.AgentRunner, bus, ledger) -> None:
        await self.agent.run_cycle()

    async def restart_no_error(self: orchestrator.AgentRunner, bus, ledger) -> None:
        if self.task:
            self.task.cancel()
            with contextlib.suppress(Exception):
                await self.task
        self.agent = self.cls(bus, ledger)
        self.start(bus, ledger)
        self.last_beat = orchestrator.time.time()

    monkeypatch.setattr(orchestrator.AgentRunner, "loop", loop_no_catch)
    monkeypatch.setattr(orchestrator.AgentRunner, "restart", restart_no_error)

    orch = orchestrator.Orchestrator(settings)
    runner = orch.runners["boom"]
    start_beat = runner.last_beat

    async def run() -> None:
        await orch.bus.start()
        runner.start(orch.bus, orch.ledger)
        orig_sleep = asyncio.sleep
        with mock.patch.object(
            orchestrator.asyncio,
            "sleep",
            new=lambda _t: orig_sleep(0.05),
        ):
            monitor = asyncio.create_task(orch._monitor())
            await orig_sleep(0.2)
            monitor.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await monitor
        if runner.task:
            runner.task.cancel()
            with contextlib.suppress(asyncio.CancelledError, BaseException):
                await runner.task
        await orch.bus.stop()

    asyncio.run(run())

    assert "restart" in events
    assert runner.last_beat > start_beat
