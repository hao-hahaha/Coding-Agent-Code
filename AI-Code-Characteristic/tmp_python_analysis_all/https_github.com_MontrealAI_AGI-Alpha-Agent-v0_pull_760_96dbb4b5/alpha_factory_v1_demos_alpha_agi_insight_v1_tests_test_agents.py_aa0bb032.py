import pytest
pytestmark = pytest.mark.skip("demo")

if False:  # type: ignore
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import (
        planning_agent,
        research_agent,
        strategy_agent,
        market_agent,
        codegen_agent,
        safety_agent,
        memory_agent,
    )
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging, config
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src.orchestrator import Ledger


async def test_agents_cycle() -> None:
    settings = config.Settings()
    bus = messaging.A2ABus(settings)
    ledger = Ledger(settings.ledger_path)
    agents = [
        planning_agent.PlanningAgent(bus, ledger),
        research_agent.ResearchAgent(bus, ledger),
        strategy_agent.StrategyAgent(bus, ledger),
        market_agent.MarketAgent(bus, ledger),
        codegen_agent.CodeGenAgent(bus, ledger),
        safety_agent.SafetyGuardianAgent(bus, ledger),
        memory_agent.MemoryAgent(bus, ledger),
    ]
    for a in agents:
        await a.run_cycle()
