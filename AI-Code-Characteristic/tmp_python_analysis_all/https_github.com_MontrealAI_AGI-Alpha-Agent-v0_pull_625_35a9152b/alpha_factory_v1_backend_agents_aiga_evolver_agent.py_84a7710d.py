"""AIGA Evolver Agent – wraps the meta-evolution demo as a domain agent.

This lightweight agent bridges :mod:`aiga_meta_evolution.meta_evolver`
into the Alpha-Factory registry so other agents can request evolutionary
runs via the shared message bus or OpenAI Agents bridge.  It gracefully
no-ops when optional heavy dependencies (torch/numpy) are absent.
"""

from __future__ import annotations

import logging
import asyncio

from backend.agents import register, _agent_base
from backend.orchestrator import _publish

try:
    from alpha_factory_v1.demos.aiga_meta_evolution.meta_evolver import MetaEvolver
    from alpha_factory_v1.demos.aiga_meta_evolution.curriculum_env import CurriculumEnv
except Exception:  # pragma: no cover - optional deps missing
    MetaEvolver = None  # type: ignore
    CurriculumEnv = None  # type: ignore

AgentBase = _agent_base()
logger = logging.getLogger(__name__)


@register(condition=lambda: MetaEvolver is not None)
class AIGAEvolverAgent(AgentBase):
    """Run one generation of AI-GA evolution per orchestrator cycle."""

    NAME = "aiga_evolver"
    CAPABILITIES = ["meta_evolution"]
    REQUIRES_API_KEY = False
    SAFE_TO_REMOVE = True
    CYCLE_SECONDS = 30

    def __init__(self) -> None:
        if MetaEvolver and CurriculumEnv:
            self.evolver = MetaEvolver(env_cls=CurriculumEnv, parallel=False)
        else:  # pragma: no cover - offline stub
            self.evolver = None
            logger.warning("MetaEvolver unavailable – AIGAEvolverAgent disabled")

    async def step(self) -> None:
        if not self.evolver:
            return
        await asyncio.to_thread(self.evolver.run_generations, 1)
        _publish(
            "aiga.best",
            {"gen": self.evolver.gen, "fitness": self.evolver.best_fitness},
        )
