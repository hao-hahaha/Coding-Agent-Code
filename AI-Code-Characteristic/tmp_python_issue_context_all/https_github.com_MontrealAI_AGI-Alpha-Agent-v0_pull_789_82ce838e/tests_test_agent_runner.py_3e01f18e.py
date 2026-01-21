import asyncio
import contextlib
from unittest.mock import patch

from alpha_factory_v1.demos.alpha_agi_insight_v1.src import orchestrator
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging


class DummyAgent:
    name = "dummy"
    CYCLE_SECONDS = 0.0

    def __init__(self) -> None:
        self.calls = 0

    async def run_cycle(self) -> None:
        self.calls += 1


def test_agent_runner_loop_publishes_heartbeat() -> None:
    agent = DummyAgent()
    runner = orchestrator.AgentRunner(agent)

    events: list[tuple[str, str]] = []

    class Bus:
        def publish(self, topic: str, env: messaging.Envelope) -> None:
            events.append(("pub", env.sender))

    class Ledger:
        def log(self, env: messaging.Envelope) -> None:
            events.append(("log", env.sender))

    bus = Bus()
    led = Ledger()

    async def run_once() -> None:
        async def _sleep(_: float) -> None:
            raise asyncio.CancelledError()

        with patch.object(asyncio, "sleep", _sleep):
            with contextlib.suppress(asyncio.CancelledError):
                await runner.loop(bus, led)

    asyncio.run(run_once())

    assert agent.calls == 1
    assert ("pub", "dummy") in events
    assert ("log", "dummy") in events
