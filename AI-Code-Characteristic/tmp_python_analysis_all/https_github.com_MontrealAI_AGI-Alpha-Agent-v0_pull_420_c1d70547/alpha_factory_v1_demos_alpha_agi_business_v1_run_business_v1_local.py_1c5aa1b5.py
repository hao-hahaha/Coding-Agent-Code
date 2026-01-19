#!/usr/bin/env python3
"""Local launcher for the Alpha‑AGI Business v1 demo.

Runs the orchestrator directly without Docker and optionally starts the
OpenAI Agents bridge when available. This script is intended for quick
experimentation on a developer workstation or inside a Colab runtime.
"""
from __future__ import annotations

import argparse
import os
import threading

import check_env


def _start_bridge(host: str) -> None:
    """Start the OpenAI Agents bridge in a background thread.

    Parameters
    ----------
    host:
        Base URL for the orchestrator that the bridge should
        communicate with (e.g. ``"http://localhost:8000"``).
    """
    try:
        from alpha_factory_v1.demos.alpha_agi_business_v1 import openai_agents_bridge
    except Exception as exc:  # pragma: no cover - optional dep
        print(f"⚠️  OpenAI bridge not available: {exc}")
        return
    _set_business_host(host=host)
    thread = threading.Thread(target=openai_agents_bridge.main, daemon=True)
    thread.start()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run alpha_agi_business_v1 locally")
    parser.add_argument(
        "--bridge",
        action="store_true",
        help="Launch OpenAI Agents bridge if available",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Expose orchestrator on this port (default: 8000)",
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Attempt automatic installation of missing packages",
    )
    parser.add_argument(
        "--wheelhouse",
        help="Optional local wheelhouse path for offline installs",
    )
    args = parser.parse_args(argv)

    check_opts: list[str] = []
    if args.auto_install:
        check_opts.append("--auto-install")
    if args.wheelhouse:
        check_opts.extend(["--wheelhouse", args.wheelhouse])

    check_env.main(check_opts)

    if args.port:
        os.environ["PORT"] = str(args.port)
        os.environ.setdefault("BUSINESS_HOST", f"http://localhost:{args.port}")

    # Configure the environment so the orchestrator picks up the ALPHA_ENABLED_AGENTS value at module import time.
    if not os.getenv("ALPHA_ENABLED_AGENTS"):
        os.environ["ALPHA_ENABLED_AGENTS"] = ",".join(
            [
                "IncorporatorAgent",
                "AlphaDiscoveryAgent",
                "AlphaOpportunityAgent",
                "AlphaExecutionAgent",
                "AlphaRiskAgent",
                "PlanningAgent",
                "ResearchAgent",
                "StrategyAgent",
                "MarketAnalysisAgent",
                "MemoryAgent",
                "SafetyAgent",
            ]
        )

    from alpha_factory_v1.demos.alpha_agi_business_v1 import alpha_agi_business_v1
    if args.bridge:
        host = os.getenv("BUSINESS_HOST", f"http://localhost:{args.port}")
        _start_bridge(host)

    alpha_agi_business_v1.main()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
