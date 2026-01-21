import asyncio
import contextlib
from unittest import mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src import orchestrator
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config


def test_run_forever_shutdown() -> None:
    settings = config.Settings(bus_port=0)
    with mock.patch.object(orchestrator.Orchestrator, "_init_agents", lambda self: []):
        orch = orchestrator.Orchestrator(settings)

    async def run() -> None:
        with mock.patch.object(orch.bus, "stop", mock.AsyncMock()) as bus_stop, \
             mock.patch.object(orch.ledger, "stop_merkle_task", mock.AsyncMock()) as merkle_stop:
            task = asyncio.create_task(orch.run_forever())
            await asyncio.sleep(0.05)
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            bus_stop.assert_awaited_once()
            merkle_stop.assert_awaited_once()

    asyncio.run(run())
