import asyncio
import contextlib
import time

from alpha_factory_v1.backend import orchestrator
from src.monitoring import metrics

class DummyRunner:
    def __init__(self) -> None:
        async def _run() -> None:
            while True:
                await asyncio.sleep(0.1)
        self.task = asyncio.create_task(_run())

def test_regression_guard(monkeypatch) -> None:
    alerts: list[str] = []
    monkeypatch.setattr(orchestrator.alerts, "send_alert", lambda m: alerts.append(m))
    runner = DummyRunner()
    runners = {"aiga_evolver": runner}

    async def drive() -> float:
        guard = asyncio.create_task(orchestrator._regression_guard(runners))
        start = time.time()
        for v in [1.0, 0.7, 0.5, 0.3]:
            metrics.dgm_best_score.set(v)
            await asyncio.sleep(0.2)
        await asyncio.sleep(0.5)
        duration = time.time() - start
        guard.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await guard
        return duration

    dur = asyncio.run(drive())
    assert runner.task.cancelled
    assert dur < 10
    assert alerts

