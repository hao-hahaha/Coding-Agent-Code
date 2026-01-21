#!/usr/bin/env python3
"""Lightweight orchestrator launcher for offline / edge deployments.

This utility wraps :mod:`alpha_factory_v1.run` with sensible defaults so that
``python edge_runner.py --agents A,B`` spins up the orchestrator in **DEV** mode
using only built‑in fallbacks (SQLite memory, in‑proc queue).  No external
services are required.

The parser inspects common environment variables (``PORT``,
``METRICS_PORT``, ``A2A_PORT`` and ``CYCLE``) so that the script can be
configured via container or system settings.  Basic validation is performed on
numeric flags to prevent invalid configuration from reaching the orchestrator.
"""
from __future__ import annotations

import argparse
import os

from alpha_factory_v1 import run as af_run, __version__


def _positive_int(name: str) -> callable:
    """Return a parser for positive integers."""

    def parser(value: str) -> int:
        try:
            iv = int(value)
        except ValueError as exc:  # pragma: no cover - argparse handles message
            raise argparse.ArgumentTypeError(f"{name} must be an integer") from exc
        if iv <= 0:
            raise argparse.ArgumentTypeError(f"{name} must be > 0")
        return iv

    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Parameters
    ----------
    argv:
        Optional argument vector. Defaults to ``sys.argv[1:]`` when ``None``.
    """

    env = os.environ
    ap = argparse.ArgumentParser(description="Alpha-Factory Edge Runner")
    ap.add_argument(
        "--agents",
        help="Comma separated list of agents to enable",
    )
    ap.add_argument(
        "--port",
        type=_positive_int("port"),
        default=int(env.get("PORT", 8000)),
        help="REST API port",
    )
    ap.add_argument(
        "--cycle",
        type=_positive_int("cycle"),
        default=int(env.get("CYCLE", 0)) or None,
        help="Override agent cycle seconds",
    )
    ap.add_argument(
        "--loglevel",
        default=None,
        help="Logging verbosity",
    )
    ap.add_argument(
        "--metrics-port",
        type=_positive_int("metrics-port"),
        default=int(env.get("METRICS_PORT", 0)) or None,
        help="Prometheus metrics port",
    )
    ap.add_argument(
        "--a2a-port",
        type=_positive_int("a2a-port"),
        default=int(env.get("A2A_PORT", 0)) or None,
        help="gRPC A2A port",
    )
    ap.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )
    ap.add_argument(
        "--list-agents",
        action="store_true",
        help="List available agents and exit",
    )
    return ap.parse_args(argv)


def main() -> None:
    args = parse_args()

    if args.version:
        print(__version__)
        return
    if args.list_agents:
        from .backend import agents
        for name in agents.list_agents():
            print(name)
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
