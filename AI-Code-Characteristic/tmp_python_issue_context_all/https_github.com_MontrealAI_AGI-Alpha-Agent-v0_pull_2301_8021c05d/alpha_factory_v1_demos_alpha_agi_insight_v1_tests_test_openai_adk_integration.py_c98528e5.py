# SPDX-License-Identifier: Apache-2.0
import sys
from pathlib import Path
import asyncio
import pytest

pytest.importorskip("openai.agents")
pytest.importorskip("google_adk")

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.strategy_agent import StrategyAgent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents.adk_summariser_agent import ADKSummariserAgent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging, logging as insight_logging


def test_oai_and_adk(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = config.Settings(openai_api_key="k")
    settings.ledger_path = str(tmp_path / "ledger.db")
    bus = messaging.A2ABus(settings)
    ledger = insight_logging.Ledger(settings.ledger_path)

    import openai.agents as oa_agents  # type: ignore
    import google_adk

    called: dict[str, str] = {}

    async def fake_run(self, prompt: str) -> str:  # pragma: no cover - async stub
        called["run"] = prompt
        return "ok"

    monkeypatch.patch.object(oa_agents.AgentContext, "run", fake_run)

    class DummyClient:
        def generate(self, prompt: str) -> str:
            called["adk"] = prompt
            return "ok"

    monkeypatch.setattr(google_adk, "Client", DummyClient)

    strat = StrategyAgent(bus, ledger)
    summariser = ADKSummariserAgent(bus, ledger)

    summariser._records.append("hello")
    env = messaging.Envelope("a", "b", {"research": "foo"}, 0.0)

    async def _run() -> None:
        await strat.handle(env)
        await summariser.run_cycle()

    asyncio.run(_run())

    assert called.get("run") == "foo"
    assert called.get("adk") == "hello"
