#!/usr/bin/env python3
"""Alpha-Factory Edge Runner.

This lightweight wrapper starts the orchestrator with edge-friendly defaults
so the stack can operate without external services or GPU acceleration.
"""
from __future__ import annotations

import argparse
import os



def main() -> None:
    parser = argparse.ArgumentParser(description="Run Alpha-Factory on edge devices")
    parser.add_argument(
        "--agents",
        default="manufacturing,energy",
        help="Comma separated list of agents to enable",
    )
    parser.add_argument(
        "--cycle",
        type=int,
        help="Override agent cycle seconds",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        help="Logging verbosity",
    )
    args = parser.parse_args()

    os.environ.setdefault("DEV_MODE", "true")
    os.environ["ALPHA_ENABLED_AGENTS"] = args.agents
    os.environ["LOGLEVEL"] = args.loglevel.upper()
    if args.cycle:
        os.environ["ALPHA_CYCLE_SECONDS"] = str(args.cycle)

    from alpha_factory_v1.backend.orchestrator import Orchestrator
    Orchestrator().run_forever()


if __name__ == "__main__":
    main()
