#!/usr/bin/env python3
"""Standalone launcher for the α‑AGI Insight demo.

This helper automatically selects the best interface for the insight
search. When the optional OpenAI Agents runtime is available and an API
key is configured the agent is registered with the runtime. Otherwise the
script falls back to the lightweight command line interface that runs the
Meta‑Agentic Tree Search locally.  Runtime dependencies are verified when
``--verify-env`` is supplied.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
from typing import List

from . import insight_demo
from . import openai_agents_bridge


def _agents_available() -> bool:
    """Return ``True`` when ``openai_agents`` can be used."""
    spec = importlib.util.find_spec("openai_agents")
    return bool(spec and os.getenv("OPENAI_API_KEY"))


def _run_offline(args: argparse.Namespace) -> None:
    sectors = insight_demo.parse_sectors(None, args.sectors)
    insight_demo.run(
        episodes=args.episodes or 5,
        exploration=args.exploration or 1.4,
        rewriter=args.rewriter,
        log_dir=Path(args.log_dir) if args.log_dir else None,
        target=args.target or 3,
        seed=args.seed,
        model=args.model,
        sectors=sectors,
    )


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Launch the α‑AGI Insight demo")
    parser.add_argument("--episodes", type=int, help="Search iterations")
    parser.add_argument("--target", type=int, help="Target sector index")
    parser.add_argument("--exploration", type=float, help="Exploration constant")
    parser.add_argument("--seed", type=int, help="Optional RNG seed")
    parser.add_argument("--model", type=str, help="Model override")
    parser.add_argument("--rewriter", choices=["random", "openai", "anthropic"], help="Rewrite strategy")
    parser.add_argument("--sectors", type=str, help="Comma-separated sectors or path to file")
    parser.add_argument("--log-dir", type=str, help="Directory for episode metrics")
    parser.add_argument("--offline", action="store_true", help="Force offline mode")
    parser.add_argument("--skip-verify", action="store_true", help="Skip environment check")
    args = parser.parse_args(argv)

    if not args.skip_verify:
        insight_demo.verify_environment()

    if args.offline or not _agents_available():
        _run_offline(args)
    else:
        openai_agents_bridge._run_runtime(
            args.episodes or 5,
            args.target or 3,
            args.model,
            args.rewriter,
            args.log_dir,
            args.sectors,
        )


if __name__ == "__main__":  # pragma: no cover
    main()
