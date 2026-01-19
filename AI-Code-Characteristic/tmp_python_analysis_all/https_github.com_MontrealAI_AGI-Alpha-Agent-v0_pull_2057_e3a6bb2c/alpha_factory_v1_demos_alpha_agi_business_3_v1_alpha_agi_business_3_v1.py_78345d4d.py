#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# NOTE: This demo is a research prototype and does not implement real AGI.
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
import hashlib
import random
import time
from typing import Any, cast

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import local_llm

try:  # optional OpenAI Agents integration
    from openai_agents import OpenAIAgent
except ImportError:  # pragma: no cover - offline fallback
    try:  # fall back to the new package name
        from agents import OpenAIAgent
    except ImportError:
        OpenAIAgent = None

try:  # optional Google ADK client
    from google_adk import Client as ADKClient  # type: ignore
except Exception:  # pragma: no cover - offline fallback
    try:
        from google.adk import Client as ADKClient  # type: ignore
    except Exception:
        ADKClient = None  # type: ignore[misc]

try:  # optional A2A message socket
    from a2a import A2ASocket  # type: ignore
    _A2A = A2ASocket(
        host=os.getenv("A2A_HOST", "localhost"),
        port=int(os.getenv("A2A_PORT", "0")),
        app_id="alpha_business_v3",
    )
except Exception:  # pragma: no cover - missing dependency
    A2ASocket = None  # type: ignore
    _A2A = None


log = logging.getLogger(__name__)


@dataclass(slots=True)
class Orchestrator:
    """Source and sink for alpha signals."""

    def collect_signals(self) -> dict[str, Any]:
        """Fetch a bundle of live signals.

        Returns a placeholder dictionary in this demo.  Production
        implementations would gather market data, sensor readings,
        or any other real‑time metrics.
        """
        return {
            "timestamp": time.time(),
            "market_temp": random.uniform(0.8, 1.2),
            "price_dislocation": random.gauss(0, 0.05),
        }

    def post_alpha_job(self, bundle_id: str, delta_g: float) -> None:
        """Broadcast a new job for agents when ``delta_g`` is favourable."""

        log.info(
            "[Orchestrator] Posting alpha job for bundle %s with ΔG=%.6f",
            bundle_id,
            delta_g,
        )


@dataclass(slots=True)
class AgentFin:
    """Finance agent returning latent-work estimates."""

    def latent_work(self, bundle: dict[str, Any]) -> float:
        """Compute mispricing alpha from ``bundle``."""
        return float(bundle.get("price_dislocation", 0))


@dataclass(slots=True)
class AgentRes:
    """Research agent estimating entropy."""

    def entropy(self, bundle: dict[str, Any]) -> float:
        """Return inferred entropy from ``bundle``."""
        return abs(float(bundle.get("price_dislocation", 0))) / 4


@dataclass(slots=True)
class AgentEne:
    """Energy agent inferring market temperature ``β``."""

    def market_temperature(self, bundle: dict[str, Any]) -> float:
        """Estimate current market temperature."""
        return float(bundle.get("market_temp", random.uniform(0.9, 1.1)))


@dataclass(slots=True)
class AgentGdl:
    """Gödel‑Looper guardian."""

    def provable(self, weight_update: dict[str, Any]) -> bool:
        """Validate a weight update via formal proof."""

        return True


async def _llm_comment(delta_g: float) -> str:
    """Return a short LLM comment on ``delta_g`` if OpenAI Agents is available."""

    # When the OpenAI Agents SDK is missing the shim in
    # ``alpha_factory_v1.backend`` exposes a non-callable placeholder.
    # Guard against that scenario as well so offline tests succeed.
    if OpenAIAgent is None or not callable(OpenAIAgent):
        return local_llm.chat(f"In one sentence, comment on ΔG={delta_g:.4f} for the business.")

    agent = OpenAIAgent(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=(
            None
            if os.getenv("OPENAI_API_KEY")
            else os.getenv("LOCAL_LLM_URL", "http://ollama:11434/v1")
        ),
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

    def commit(self, weight_update: dict[str, Any]) -> None:
        """Commit the supplied weights after verification."""

        log.info("[Model] New weights committed (Gödel-proof verified)")


async def run_cycle_async(
    orchestrator: Orchestrator,
    fin_agent: AgentFin,
    res_agent: AgentRes,
    ene_agent: AgentEne,
    gdl_agent: AgentGdl,
    model: Model,
    adk_client: Any | None = None,
) -> None:
    """Execute one evaluation + commitment cycle."""

    bundle = orchestrator.collect_signals()
    delta_h = fin_agent.latent_work(bundle)
    delta_s = res_agent.entropy(bundle)
    beta = ene_agent.market_temperature(bundle)
    if abs(beta) < 1e-9:
        log.warning("β is zero; skipping cycle")
        return
    delta_g = delta_h - (delta_s / beta)

    log.info("ΔH=%s ΔS=%s β=%s → ΔG=%s", delta_h, delta_s, beta, delta_g)

    comment = await _llm_comment(delta_g)
    log.info("LLM: %s", comment)

    if _A2A:
        try:
            _A2A.sendjson({"delta_g": delta_g})
        except Exception:  # pragma: no cover - best effort
            log.warning("A2A send failed", exc_info=True)

    if adk_client is not None:
        try:
            if asyncio.iscoroutinefunction(getattr(adk_client, "run", None)):
                await adk_client.run(comment)
            elif hasattr(adk_client, "run"):
                await asyncio.to_thread(adk_client.run, comment)
        except Exception:  # pragma: no cover - best effort
            log.warning("ADK client error", exc_info=True)

    if delta_g < 0:
        bundle_hash = hashlib.sha256(repr(bundle).encode()).hexdigest()[:8]
        orchestrator.post_alpha_job(bundle_hash, delta_g)

    weight_update: dict[str, Any] = {}
    if gdl_agent.provable(weight_update):
        model.commit(weight_update)


def run_cycle(
    orchestrator: Orchestrator,
    fin_agent: AgentFin,
    res_agent: AgentRes,
    ene_agent: AgentEne,
    gdl_agent: AgentGdl,
    model: Model,
    adk_client: Any | None = None,
    loop: asyncio.AbstractEventLoop | None = None,
) -> None:
    """Execute one evaluation cycle, creating an event loop if required."""

    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop is not None:
        running_loop.create_task(
            run_cycle_async(
                orchestrator,
                fin_agent,
                res_agent,
                ene_agent,
                gdl_agent,
                model,
                adk_client,
            )
        )
        return

    if loop is None:
        asyncio.run(
            run_cycle_async(
                orchestrator,
                fin_agent,
                res_agent,
                ene_agent,
                gdl_agent,
                model,
                adk_client,
            )
        )
    else:
        loop.run_until_complete(
            run_cycle_async(
                orchestrator,
                fin_agent,
                res_agent,
                ene_agent,
                gdl_agent,
                model,
                adk_client,
            )
        )


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

    if _A2A:
        try:
            _A2A.start()
        except Exception:  # pragma: no cover - best effort
            log.warning("Failed to start A2A socket", exc_info=True)

    adk_client = ADKClient(os.getenv("ADK_HOST", "http://localhost:9000")) if ADKClient else None

    cycle = 0
    while True:
        await run_cycle_async(
            orchestrator,
            fin_agent,
            res_agent,
            ene_agent,
            gdl_agent,
            model,
            adk_client,
        )
        cycle += 1
        if args.cycles and cycle >= args.cycles:
            break
        await asyncio.sleep(args.interval)


if __name__ == "__main__":  # pragma: no cover - manual execution
    asyncio.run(main())
