#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Alpha‑AGI Business v1 demo.

Bootstraps a minimal Alpha‑Factory orchestrator with two stub agents.
The demo operates fully offline but upgrades to cloud LLM tooling
automatically when ``OPENAI_API_KEY`` is present.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
from pathlib import Path

# allow running this script directly from its folder
SCRIPT_DIR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from alpha_factory_v1.backend import orchestrator  # noqa: E402
from alpha_factory_v1.backend.agents import (  # noqa: E402
    AGENT_REGISTRY,
    AgentMetadata,
    register_agent,
)
from alpha_factory_v1.backend.agents.base import AgentBase  # noqa: E402
from alpha_factory_v1.backend.agents.planning_agent import PlanningAgent  # noqa: E402
from alpha_factory_v1.backend.agents.research_agent import ResearchAgent  # noqa: E402
from alpha_factory_v1.backend.agents.strategy_agent import StrategyAgent  # noqa: E402
from alpha_factory_v1.backend.agents.market_analysis_agent import MarketAnalysisAgent  # noqa: E402
from alpha_factory_v1.backend.agents.memory_agent import MemoryAgent  # noqa: E402
from alpha_factory_v1.backend.agents.safety_agent import SafetyAgent  # noqa: E402
from alpha_factory_v1.backend.llm_provider import chat as llm_provider  # noqa: E402


class IncorporatorAgent(AgentBase):
    """Toy agent that emits a one‑time incorporation event."""

    NAME = "incorporator"
    CAPABILITIES = ["incorporate"]
    __slots__ = ()

    async def step(self) -> None:
        await self.publish("alpha.business", {"msg": "company incorporated"})


class AlphaDiscoveryAgent(AgentBase):
    """Stub agent that emits a placeholder alpha opportunity."""

    NAME = "alpha_discovery"
    CAPABILITIES = ["discover"]
    CYCLE_SECONDS = 120
    __slots__ = ()

    async def step(self) -> None:
        prompt = "Suggest one brief, plausible market inefficiency suitable for a demo."
        try:
            summary = await llm_provider(prompt, max_tokens=50)
        except Exception as exc:  # pragma: no cover - LLM optional
            summary = f"demo opportunity (llm error: {exc})"
        await self.publish("alpha.discovery", {"alpha": summary})


class AlphaOpportunityAgent(AgentBase):
    """Stub agent emitting a sample market inefficiency."""

    NAME = "alpha_opportunity"
    CAPABILITIES = ["opportunity"]
    CYCLE_SECONDS = 300
    __slots__ = ("_opportunities", "_yf", "_symbol", "_select_best", "_top_n")

    def __init__(self) -> None:
        super().__init__()
        env_path = os.getenv("ALPHA_OPPS_FILE")
        path = Path(env_path) if env_path else Path(__file__).with_name("examples") / "alpha_opportunities.json"
        try:
            self._opportunities = json.loads(Path(path).read_text(encoding="utf-8"))
        except FileNotFoundError:  # pragma: no cover - fallback when file missing
            self._opportunities = [{"alpha": "generic supply-chain inefficiency", "score": 0}]
        except json.JSONDecodeError:  # pragma: no cover - fallback for invalid JSON
            self._opportunities = [{"alpha": "generic supply-chain inefficiency", "score": 0}]

        # Optional deterministic ranking when ALPHA_BEST_ONLY=1
        self._select_best = os.getenv("ALPHA_BEST_ONLY", "0") == "1"

        # Allow publishing the top-N opportunities
        try:
            self._top_n = max(0, int(os.getenv("ALPHA_TOP_N", "0")))
        except ValueError:
            self._top_n = 0

        if self._select_best or self._top_n:
            self._opportunities.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Optional live price feed via yfinance
        self._symbol = os.getenv("YFINANCE_SYMBOL")
        if self._symbol:
            try:  # soft dependency
                import yfinance as yf  # type: ignore

                self._yf = yf
            except Exception:  # pragma: no cover - fallback when yfinance missing
                self._yf = None
        else:
            self._yf = None

    async def step(self) -> None:
        if self._symbol and self._yf:
            try:
                data = self._yf.download(self._symbol, period="1d", progress=False)
                price = data["Close"].iloc[-1]
                await self.publish(
                    "alpha.opportunity",
                    {"symbol": self._symbol, "price": float(price)},
                )
                return
            except Exception as e:  # pragma: no cover - network/unavailable
                logging.error(
                    "Failed to download live price feed for symbol %s: %s",
                    self._symbol,
                    e,
                    exc_info=True,
                )

        if self._top_n and self._opportunities:
            for item in self._opportunities[: self._top_n]:
                await self.publish("alpha.opportunity", item)
            return

        if self._select_best and self._opportunities:
            choice = self._opportunities[0]
        else:
            choice = random.choice(self._opportunities)
        await self.publish("alpha.opportunity", choice)


class AlphaExecutionAgent(AgentBase):
    """Stub agent converting an opportunity into an executed trade."""

    NAME = "alpha_execution"
    CAPABILITIES = ["execute"]
    CYCLE_SECONDS = 180
    __slots__ = ()

    async def step(self) -> None:
        await self.publish("alpha.execution", {"alpha": "order executed"})


class AlphaRiskAgent(AgentBase):
    """Stub agent performing a placeholder risk assessment."""

    NAME = "alpha_risk"
    CAPABILITIES = ["risk"]
    CYCLE_SECONDS = 240
    __slots__ = ()

    async def step(self) -> None:
        await self.publish("alpha.risk", {"risk": "risk level nominal"})


class AlphaComplianceAgent(AgentBase):
    """Stub agent performing a simple compliance check."""

    NAME = "alpha_compliance"
    CAPABILITIES = ["compliance"]
    CYCLE_SECONDS = 300
    __slots__ = ()

    async def step(self) -> None:
        await self.publish("alpha.compliance", {"status": "ok"})


class AlphaPortfolioAgent(AgentBase):
    """Stub agent summarising portfolio state.

    This agent publishes a static placeholder summary of the portfolio state.
    In a production implementation, this would dynamically summarize executed positions.
    """

    NAME = "alpha_portfolio"
    CAPABILITIES = ["portfolio"]
    CYCLE_SECONDS = 300
    __slots__ = ()

    async def step(self) -> None:
        await self.publish(
            "alpha.portfolio",
            {"summary": "nominal", "note": "This is a placeholder summary."},
        )


def _register_if_needed(meta: AgentMetadata) -> None:
    """Register ``meta`` unless already present."""

    if meta.name in AGENT_REGISTRY:
        return
    register_agent(meta)


def register_demo_agents() -> None:
    """Register built-in demo agents with the framework."""

    _register_if_needed(
        AgentMetadata(
            name=IncorporatorAgent.NAME,
            cls=IncorporatorAgent,
            version="1.0.0",
            capabilities=IncorporatorAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=AlphaDiscoveryAgent.NAME,
            cls=AlphaDiscoveryAgent,
            version="1.0.0",
            capabilities=AlphaDiscoveryAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=AlphaOpportunityAgent.NAME,
            cls=AlphaOpportunityAgent,
            version="1.0.0",
            capabilities=AlphaOpportunityAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=AlphaExecutionAgent.NAME,
            cls=AlphaExecutionAgent,
            version="1.0.0",
            capabilities=AlphaExecutionAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=AlphaRiskAgent.NAME,
            cls=AlphaRiskAgent,
            version="1.0.0",
            capabilities=AlphaRiskAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=AlphaComplianceAgent.NAME,
            cls=AlphaComplianceAgent,
            version="1.0.0",
            capabilities=AlphaComplianceAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=AlphaPortfolioAgent.NAME,
            cls=AlphaPortfolioAgent,
            version="1.0.0",
            capabilities=AlphaPortfolioAgent.CAPABILITIES,
        )
    )

    # --- additional role agents ---
    _register_if_needed(
        AgentMetadata(
            name=PlanningAgent.NAME,
            cls=PlanningAgent,
            version="1.0.0",
            capabilities=PlanningAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=ResearchAgent.NAME,
            cls=ResearchAgent,
            version="1.0.0",
            capabilities=ResearchAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=StrategyAgent.NAME,
            cls=StrategyAgent,
            version="1.0.0",
            capabilities=StrategyAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=MarketAnalysisAgent.NAME,
            cls=MarketAnalysisAgent,
            version="1.0.0",
            capabilities=MarketAnalysisAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=MemoryAgent.NAME,
            cls=MemoryAgent,
            version="1.0.0",
            capabilities=MemoryAgent.CAPABILITIES,
        )
    )

    _register_if_needed(
        AgentMetadata(
            name=SafetyAgent.NAME,
            cls=SafetyAgent,
            version="1.0.0",
            capabilities=SafetyAgent.CAPABILITIES,
        )
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the α‑AGI Business v1 demo")
    parser.add_argument(
        "--loglevel",
        default=os.getenv("LOGLEVEL", "INFO"),
        help="Logging verbosity (default: INFO)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Launch the orchestrator with the demo agent registered."""

    args = _parse_args(argv)
    logging.basicConfig(
        level=args.loglevel.upper(),
        format="%(asctime)s %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    register_demo_agents()

    try:
        orchestrator.Orchestrator().run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":  # pragma: no cover - manual execution
    import sys

    main(sys.argv[1:])
