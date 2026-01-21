"""OpenAI Agents SDK bridge for the AI-GA Meta-Evolution demo.

This script registers a minimal agent capable of driving the evolutionary
loop via the OpenAI Agents runtime. It works fully offline when no
``OPENAI_API_KEY`` is configured by falling back to the local Ollama
instance started by ``run_aiga_demo.sh``.
"""
from __future__ import annotations

import os
from openai_agents import Agent, AgentRuntime, OpenAIAgent, Tool

try:
    from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch
    ADK_AVAILABLE = True
except Exception:  # pragma: no cover - optional
    ADK_AVAILABLE = False

from meta_evolver import MetaEvolver
from curriculum_env import CurriculumEnv


# ---------------------------------------------------------------------------
# LLM setup -----------------------------------------------------------------
# ---------------------------------------------------------------------------
LLM = OpenAIAgent(
    model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=(None if os.getenv("OPENAI_API_KEY") else os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")),
)

# single MetaEvolver instance reused across tool invocations
EVOLVER = MetaEvolver(env_cls=CurriculumEnv, llm=LLM)


@Tool(name="evolve", description="Run N generations of evolution")
async def evolve(generations: int = 1) -> str:
    EVOLVER.run_generations(generations)
    return EVOLVER.latest_log()


@Tool(name="best_alpha", description="Return current best architecture")
async def best_alpha() -> dict:
    return {
        "architecture": EVOLVER.best_architecture,
        "fitness": EVOLVER.best_fitness,
    }


@Tool(name="checkpoint", description="Persist current state to disk")
async def checkpoint() -> str:
    EVOLVER.save()
    return "checkpoint saved"


@Tool(name="reset", description="Reset evolution to generation zero")
async def reset() -> str:
    EVOLVER.reset()
    return "evolver reset"


class EvolverAgent(Agent):
    """Tiny agent exposing the meta-evolver tools."""

    name = "aiga_evolver"
    tools = [evolve, best_alpha, checkpoint, reset]

    async def policy(self, obs, ctx):  # type: ignore[override]
        gens = int(obs.get("gens", 1)) if isinstance(obs, dict) else 1
        await evolve(gens)
        return await best_alpha()


def main() -> None:
    runtime = AgentRuntime(api_key=None)
    agent = EvolverAgent()
    runtime.register(agent)
    print("Registered EvolverAgent with runtime")

    if ADK_AVAILABLE:
        auto_register([agent])
        maybe_launch()
        print("EvolverAgent exposed via ADK gateway")

    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
