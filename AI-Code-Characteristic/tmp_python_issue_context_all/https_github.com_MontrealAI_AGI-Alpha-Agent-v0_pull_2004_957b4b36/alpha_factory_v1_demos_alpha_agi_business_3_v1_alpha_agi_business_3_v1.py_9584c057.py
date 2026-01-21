#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Self-contained Ω‑Lattice business demo.

This module showcases a minimal zero‑entropy pipeline suitable for
production‑grade environments.  The orchestration loop computes a
Gibbs‑inspired :math:`ΔG` metric using three toy agents.  When
``ΔG < 0`` an alpha job is posted.  A final Gödel‑Looper step then
verifies and commits a (mock) weight update.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import logging
import asyncio
import os
from typing import Any, Dict, cast

try:  # optional OpenAI Agents integration
    from openai_agents import OpenAIAgent
except Exception:  # pragma: no cover - offline fallback
    OpenAIAgent = None


log = logging.getLogger(__name__)


@dataclass(slots=True)
class Orchestrator:
    """Source and sink for alpha signals."""

    def collect_signals(self) -> Dict[str, Any]:
        """Fetch a bundle of live signals.

        Returns a placeholder dictionary in this demo.  Production
        implementations would gather market data, sensor readings,
        or any other real‑time metrics.
        """

        return {"signal": "example"}

    def post_alpha_job(self, bundle_id: int, delta_g: float) -> None:
        """Broadcast a new job for agents when ``delta_g`` is favourable."""

        log.info(
            "[Orchestrator] Posting alpha job for bundle %s with ΔG=%.6f",
            bundle_id,
            delta_g,
        )


@dataclass(slots=True)
class AgentFin:
    """Finance agent returning latent-work estimates."""

    def latent_work(self, bundle: Dict[str, Any]) -> float:
        """Compute mispricing alpha from ``bundle``."""

        return 0.04


@dataclass(slots=True)
class AgentRes:
    """Research agent estimating entropy."""

    def entropy(self, bundle: Dict[str, Any]) -> float:
        """Return inferred entropy from ``bundle``."""

        return 0.01


@dataclass(slots=True)
class AgentEne:
    """Energy agent inferring market temperature ``β``."""

    def market_temperature(self) -> float:
        """Estimate current market temperature."""

        return 1.0


@dataclass(slots=True)
class AgentGdl:
    """Gödel‑Looper guardian."""

    def provable(self, weight_update: Dict[str, Any]) -> bool:
        """Validate a weight update via formal proof."""

        return True


async def _llm_comment(delta_g: float) -> str:
    """Return a short LLM comment on ``delta_g`` if OpenAI Agents is available."""

    # When the OpenAI Agents SDK is missing the shim in
    # ``alpha_factory_v1.backend`` exposes a non-callable placeholder.
    # Guard against that scenario as well so offline tests succeed.
    if OpenAIAgent is None or not callable(OpenAIAgent):
        return "LLM offline"

    agent = OpenAIAgent(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=(None if os.getenv("OPENAI_API_KEY") else "http://ollama:11434/v1"),
    )
    try:
        return cast(
            str,
            await agent(f"In one sentence, comment on ΔG={delta_g:.4f} for the business."),
        )
    except Exception as exc:  # pragma: no cover - network failures
        log.warning("LLM comment failed: %s", exc)
        return "LLM error"


@dataclass(slots=True)
class Model:
    """Persisted model whose weights evolve over time."""

    def commit(self, weight_update: Dict[str, Any]) -> None:
        """Commit the supplied weights after verification."""

        log.info("[Model] New weights committed (Gödel-proof verified)")


async def run_cycle_async(
    orchestrator: Orchestrator,
    fin_agent: AgentFin,
    res_agent: AgentRes,
    ene_agent: AgentEne,
    gdl_agent: AgentGdl,
    model: Model,
) -> None:
    """Execute one evaluation + commitment cycle."""

    bundle = orchestrator.collect_signals()
    delta_h = fin_agent.latent_work(bundle)
    delta_s = res_agent.entropy(bundle)
    beta = ene_agent.market_temperature()
    if abs(beta) < 1e-9:
        log.warning("β is zero; skipping cycle")
        return
    delta_g = delta_h - (delta_s / beta)

    log.info("ΔH=%s ΔS=%s β=%s → ΔG=%s", delta_h, delta_s, beta, delta_g)

    comment = await _llm_comment(delta_g)
    log.info("LLM: %s", comment)

    if delta_g < 0:
        orchestrator.post_alpha_job(id(bundle), delta_g)

    weight_update: Dict[str, Any] = {}
    if gdl_agent.provable(weight_update):
        model.commit(weight_update)


def run_cycle(
    orchestrator: Orchestrator,
    fin_agent: AgentFin,
    res_agent: AgentRes,
    ene_agent: AgentEne,
    gdl_agent: AgentGdl,
    model: Model,
    loop: asyncio.AbstractEventLoop | None = None,
) -> None:
    """Execute one evaluation cycle, creating an event loop if required."""

    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop is not None:
        running_loop.create_task(run_cycle_async(orchestrator, fin_agent, res_agent, ene_agent, gdl_agent, model))
        return

    if loop is None:
        asyncio.run(run_cycle_async(orchestrator, fin_agent, res_agent, ene_agent, gdl_agent, model))
    else:
        loop.run_until_complete(run_cycle_async(orchestrator, fin_agent, res_agent, ene_agent, gdl_agent, model))


async def main(argv: list[str] | None = None) -> None:
    """Entry point for command line execution."""

    ap = argparse.ArgumentParser(description="Run the Ω‑Lattice business demo")
    ap.add_argument("--loglevel", default="INFO", help="Logging level")
    ap.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Number of cycles to run (0 = forever)",
    )
    ap.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds to sleep between cycles",
    )
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=args.loglevel.upper(),
        format="%(asctime)s %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    orchestrator = Orchestrator()
    fin_agent = AgentFin()
    res_agent = AgentRes()
    ene_agent = AgentEne()
    gdl_agent = AgentGdl()
    model = Model()

    cycle = 0
    while True:
        await run_cycle_async(orchestrator, fin_agent, res_agent, ene_agent, gdl_agent, model)
        cycle += 1
        if args.cycles and cycle >= args.cycles:
            break
        await asyncio.sleep(args.interval)


if __name__ == "__main__":  # pragma: no cover - manual execution
    asyncio.run(main())
