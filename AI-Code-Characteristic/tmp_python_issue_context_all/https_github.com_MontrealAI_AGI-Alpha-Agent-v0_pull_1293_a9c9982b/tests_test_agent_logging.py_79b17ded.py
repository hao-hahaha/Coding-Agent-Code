import asyncio
from unittest import mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import (
    market_agent,
    strategy_agent,
    research_agent,
)
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging, local_llm
from tests.test_agent_handle_methods import DummyBus, DummyLedger


class DummyCtx:
    async def run(self, *a, **k):
        raise RuntimeError("boom")


def test_market_agent_logs_exception():
    cfg = config.Settings(bus_port=0, openai_api_key="k")
    bus = DummyBus(cfg)
    led = DummyLedger()
    agent = market_agent.MarketAgent(bus, led)
    agent.oai_ctx = DummyCtx()
    env = messaging.Envelope("strategy", "market", {"strategy": "foo"}, 0.0)
    with mock.patch.object(market_agent.log, "warning") as warn:
        asyncio.run(agent.handle(env))
        warn.assert_called_once()


def test_strategy_agent_logs_exception(monkeypatch):
    cfg = config.Settings(bus_port=0)
    bus = DummyBus(cfg)
    led = DummyLedger()
    agent = strategy_agent.StrategyAgent(bus, led)

    monkeypatch.setattr(local_llm, "chat", lambda *_: (_ for _ in ()).throw(RuntimeError("boom")))
    env = messaging.Envelope("research", "strategy", {"research": "foo"}, 0.0)
    with mock.patch.object(strategy_agent.log, "warning") as warn:
        asyncio.run(agent.handle(env))
        warn.assert_called_once()


def test_research_agent_logs_exception():
    cfg = config.Settings(bus_port=0, openai_api_key="k")
    bus = DummyBus(cfg)
    led = DummyLedger()
    agent = research_agent.ResearchAgent(bus, led)
    agent.oai_ctx = DummyCtx()
    env = messaging.Envelope("planning", "research", {"plan": "bar"}, 0.0)
    with mock.patch.object(research_agent.log, "warning") as warn:
        asyncio.run(agent.handle(env))
        warn.assert_called_once()

