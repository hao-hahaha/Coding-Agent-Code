import asyncio
import pathlib
from typing import List

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import (
    planning_agent,
    research_agent,
    strategy_agent,
    market_agent,
    codegen_agent,
    safety_agent,
    memory_agent,
)
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger


def test_agent_pipeline(tmp_path: pathlib.Path) -> None:
    settings = config.Settings()
    settings.ledger_path = str(tmp_path / "ledger.db")
    bus = messaging.A2ABus(settings)
    ledger = Ledger(settings.ledger_path)

    plan_msgs: List[messaging.Envelope] = []
    bus.subscribe("research", plan_msgs.append)

    strat_msgs: List[messaging.Envelope] = []
    bus.subscribe("strategy", strat_msgs.append)

    market_msgs: List[messaging.Envelope] = []
    bus.subscribe("market", market_msgs.append)

    code_msgs: List[messaging.Envelope] = []
    bus.subscribe("codegen", code_msgs.append)

    safety_in: List[messaging.Envelope] = []
    bus.subscribe("safety", safety_in.append)

    memory_msgs: List[messaging.Envelope] = []
    bus.subscribe("memory", memory_msgs.append)

    mem_agent = memory_agent.MemoryAgent(bus, ledger)
    agents = [
        planning_agent.PlanningAgent(bus, ledger),
        research_agent.ResearchAgent(bus, ledger),
        strategy_agent.StrategyAgent(bus, ledger),
        market_agent.MarketAgent(bus, ledger),
        codegen_agent.CodeGenAgent(bus, ledger),
        safety_agent.SafetyGuardianAgent(bus, ledger),
        mem_agent,
    ]

    async def _run() -> None:
        await agents[0].run_cycle()
        assert plan_msgs, "planning agent did not emit research plan"

        await agents[1].handle(plan_msgs[0])
        assert strat_msgs, "research agent did not emit strategy payload"

        await agents[2].handle(strat_msgs[0])
        assert market_msgs, "strategy agent did not emit market analysis"

        await agents[3].handle(market_msgs[0])
        assert code_msgs, "market agent did not emit code generation task"

        await agents[4].handle(code_msgs[0])
        assert safety_in, "codegen agent did not emit safety event"

        await agents[5].handle(safety_in[0])
        assert memory_msgs, "safety agent did not emit memory payload"

        await mem_agent.handle(memory_msgs[0])
        assert mem_agent.records, "memory agent did not store payload"
        ledger.close()

    asyncio.run(_run())
