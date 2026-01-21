#!/usr/bin/env python3
"""OpenAI Agents SDK bridge for the α‑AGI Insight demo.

This utility exposes the Meta‑Agentic Tree Search loop used by
:mod:`alpha_agi_insight_v0` through the OpenAI Agents runtime.
It gracefully degrades to offline mode when the optional
``openai-agents`` package is missing or the environment lacks API keys.
"""
from __future__ import annotations

import os
import argparse
import importlib.util
import sys
import pathlib

DEFAULT_MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o")

# Prefix used when running without the optional ``openai-agents`` package.
# Makes it easy for unit tests and calling code to detect the offline path.
FALLBACK_MODE_PREFIX = "fallback_mode_active: "


if __package__ is None:  # pragma: no cover - allow direct execution
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
    __package__ = "alpha_factory_v1.demos.alpha_agi_insight_v0"

from .insight_demo import run, verify_environment

try:
    _spec = importlib.util.find_spec("openai_agents")
except ValueError:  # loaded stub with missing spec
    _spec = None
has_oai = _spec is not None

if has_oai:
    from openai_agents import Agent, AgentRuntime, Tool  # type: ignore

    @Tool(name="run_insight_search", description="Run the α‑AGI Insight demo")
    async def run_insight_search(
        episodes: int = 5,
        target: int = 3,
        model: str | None = None,
        rewriter: str | None = None,
        sectors: str | None = None,
    ) -> str:
        if model:
            os.environ.setdefault("OPENAI_MODEL", model)
        if rewriter:
            os.environ.setdefault("MATS_REWRITER", rewriter)
        result = run(
            episodes=episodes,
            target=target,
            model=model,
            rewriter=rewriter,
            sectors=(sectors.split(",") if sectors else None),
        )
        return result

    class InsightAgent(Agent):
        name = "agi_insight_helper"
        tools = [run_insight_search]

        async def policy(self, obs, _ctx):  # type: ignore[override]
            params = obs if isinstance(obs, dict) else {}
            return await run_insight_search(
                episodes=int(params.get("episodes", 5)),
                target=int(params.get("target", 3)),
                model=params.get("model"),
                rewriter=params.get("rewriter"),
                sectors=params.get("sectors"),
            )

    def _run_runtime(
        episodes: int, target: int, model: str | None = None, rewriter: str | None = None
    ) -> None:
        if model:
            os.environ.setdefault("OPENAI_MODEL", model)
        if rewriter:
            os.environ.setdefault("MATS_REWRITER", rewriter)
        runtime = AgentRuntime(api_key=os.getenv("OPENAI_API_KEY"))
        agent = InsightAgent()
        runtime.register(agent)
        try:
            from alpha_factory_v1.backend import adk_bridge

            if adk_bridge.adk_enabled():
                adk_bridge.auto_register([agent])
                adk_bridge.maybe_launch()
            else:
                logger.info("ADK gateway disabled.")
        except ImportError as exc:  # pragma: no cover - optional ADK
            logger.warning(f"ADK bridge import failed: {exc}")
        except AttributeError as exc:  # pragma: no cover - optional ADK
            logger.error(f"ADK bridge attribute error: {exc}")

        logger.info("Registered InsightAgent with runtime")
        runtime.run()
else:

    async def run_insight_search(
        episodes: int = 5,
        target: int = 3,
        model: str | None = None,
        rewriter: str | None = None,
        sectors: str | None = None,
    ) -> str:
        summary = run(
            episodes=episodes,
            target=target,
            model=model,
            rewriter=rewriter,
            sectors=(sectors.split(",") if sectors else None),
        )
        return f"{FALLBACK_MODE_PREFIX}{summary}"

    def _run_runtime(
        episodes: int, target: int, model: str | None = None, rewriter: str | None = None
    ) -> None:
        print("openai-agents package is missing. Running offline demo...")
        run(episodes=episodes, target=target, model=model, rewriter=rewriter)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="OpenAI Agents bridge for the α‑AGI Insight demo")
    parser.add_argument("--episodes", type=int, default=5, help="Search episodes when offline")
    parser.add_argument("--target", type=int, default=3, help="Target sector index when offline")
    parser.add_argument("--model", type=str, help="Model name override")
    parser.add_argument(
        "--rewriter",
        choices=["random", "openai", "anthropic"],
        help="Rewrite strategy",
    )
    parser.add_argument("--sectors", type=str, help="Comma-separated sector names")
    parser.add_argument(
        "--enable-adk",
        action="store_true",
        help="Enable the Google ADK gateway",
    )
    parser.add_argument(
        "--verify-env",
        action="store_true",
        help="Check runtime dependencies before launching",
    )
    args = parser.parse_args(argv)

    if args.verify_env:
        verify_environment()

    if args.enable_adk:
        os.environ.setdefault("ALPHA_FACTORY_ENABLE_ADK", "true")

    _run_runtime(args.episodes, args.target, args.model, args.rewriter)


__all__ = [
    "DEFAULT_MODEL_NAME",
    "has_oai",
    "run_insight_search",
    "main",
]


if __name__ == "__main__":  # pragma: no cover
    main()
