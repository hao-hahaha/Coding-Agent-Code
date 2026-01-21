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
import logging
import os

from typing import Callable

from alpha_factory_v1 import run as af_run, __version__

log = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    """Return ``int`` environment value or ``default`` if conversion fails."""

    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        log.warning("Invalid %s=%r, using default %s", name, val, default)
        return default


def _positive_int(name: str) -> Callable[[str], int]:
    """Return a parser for positive integers.

    Parameters
    ----------
    name:
        Command line option name used in error messages.
    """

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

    ap = argparse.ArgumentParser(description="Alpha-Factory Edge Runner")
    ap.add_argument(
        "--agents",
        help="Comma separated list of agents to enable",
    )
    port_default = _env_int("PORT", 8000)
    if port_default <= 0:
        port_default = 8000
    ap.add_argument(
        "--port",
        type=_positive_int("port"),
        default=port_default,
        help="REST API port",
    )
    ap.add_argument(
        "--cycle",
        type=_positive_int("cycle"),
        default=_env_int("CYCLE", 0) or None,
        help="Override agent cycle seconds",
    )
    ap.add_argument(
        "--loglevel",
        default=None,
        help="Logging verbosity",
    )
    metrics_default = _env_int("METRICS_PORT", 0)
    if metrics_default <= 0:
        metrics_default = 0
    ap.add_argument(
        "--metrics-port",
        type=_positive_int("metrics-port"),
        default=metrics_default or None,
        help="Prometheus metrics port",
    )
    a2a_default = _env_int("A2A_PORT", 0)
    if a2a_default <= 0:
        a2a_default = 0
    ap.add_argument(
        "--a2a-port",
        type=_positive_int("a2a-port"),
        default=a2a_default or None,
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

    cli = ["--dev", "--port", str(args.port)]
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
