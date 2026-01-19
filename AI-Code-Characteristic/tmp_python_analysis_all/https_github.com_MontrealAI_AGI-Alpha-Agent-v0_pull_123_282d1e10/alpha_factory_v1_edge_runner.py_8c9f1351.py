#!/usr/bin/env python3
"""Lightweight orchestrator launcher for offline / edge deployments.

This utility wraps :mod:`alpha_factory_v1.run` with sensible defaults so that
`python edge_runner.py --agents A,B` spins up the orchestrator in **DEV** mode
using only built‑in fallbacks (SQLite memory, in‑proc queue).  No external
services are required.
"""
from __future__ import annotations

import argparse
import os

from alpha_factory_v1 import run as af_run, __version__


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Alpha-Factory Edge Runner")
    ap.add_argument(
        "--agents",
        help="Comma separated list of agents to enable",
    )
    ap.add_argument(
        "--port",
        type=int,
        default=8000,
        help="REST API port (default: 8000)",
    )
    ap.add_argument(
        "--cycle",
        type=int,
        help="Override agent cycle seconds",
    )
    ap.add_argument(
        "--loglevel",
        default="INFO",
        help="Logging verbosity",
    )
    ap.add_argument(
        "--metrics-port",
        type=int,
        help="Prometheus metrics port",
    )
    ap.add_argument(
        "--a2a-port",
        type=int,
        help="gRPC A2A port",
    )
    ap.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    if args.version:
        print(__version__)
        return

    cli = ["--dev", f"--port", str(args.port)]
    if args.metrics_port:
        cli += ["--metrics-port", str(args.metrics_port)]
    if args.a2a_port:
        cli += ["--a2a-port", str(args.a2a_port)]
    if args.agents:
        cli += ["--enabled", args.agents]
    if args.cycle:
        cli += ["--cycle", str(args.cycle)]
    if args.loglevel:
        cli += ["--loglevel", args.loglevel]

    ns = af_run.parse_args(cli)
    af_run.apply_env(ns)

    os.environ.setdefault("PGHOST", "sqlite")

    af_run.run()


if __name__ == "__main__":
    main()
