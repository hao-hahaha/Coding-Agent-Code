# SPDX-License-Identifier: Apache-2.0
"""Standalone launcher for the Alpha‑Factory orchestrator."""

from __future__ import annotations

import argparse
import os

from .. import __version__
from ..scripts.preflight import main as _preflight
from .orchestrator import Orchestrator


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Alpha-Factory backend entry point")
    parser.add_argument("--dev", action="store_true", help="Enable development mode (DEV_MODE)")
    parser.add_argument("--preflight", action="store_true", help="Run environment checks and exit")
    parser.add_argument("--port", type=int, help="REST API port (PORT)")
    parser.add_argument("--metrics-port", type=int, help="Prometheus metrics port (METRICS_PORT)")
    parser.add_argument("--a2a-port", type=int, help="A2A gRPC port (A2A_PORT)")
    parser.add_argument("--disable-tls", action="store_true", help="Disable TLS for gRPC (INSECURE_DISABLE_TLS)")
    parser.add_argument("--kafka-broker", help="Kafka bootstrap servers (ALPHA_KAFKA_BROKER)")
    parser.add_argument("--cycle-seconds", type=int, help="Default agent cycle period (ALPHA_CYCLE_SECONDS)")
    parser.add_argument("--max-cycle-sec", type=int, help="Hard limit per agent run (MAX_CYCLE_SEC)")
    parser.add_argument("--enabled", help="Comma-separated list of enabled agents (ALPHA_ENABLED_AGENTS)")
    parser.add_argument("--loglevel", default="INFO", help="Logging level (LOGLEVEL)")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    return parser.parse_args()


def _apply_env(args: argparse.Namespace) -> None:
    if args.dev:
        os.environ["DEV_MODE"] = "true"
    if args.port is not None:
        os.environ["PORT"] = str(args.port)
    if args.metrics_port is not None:
        os.environ["METRICS_PORT"] = str(args.metrics_port)
    if args.a2a_port is not None:
        os.environ["A2A_PORT"] = str(args.a2a_port)
    if args.disable_tls:
        os.environ["INSECURE_DISABLE_TLS"] = "true"
    if args.kafka_broker is not None:
        os.environ["ALPHA_KAFKA_BROKER"] = args.kafka_broker
    if args.cycle_seconds is not None:
        os.environ["ALPHA_CYCLE_SECONDS"] = str(args.cycle_seconds)
    if args.max_cycle_sec is not None:
        os.environ["MAX_CYCLE_SEC"] = str(args.max_cycle_sec)
    if args.enabled is not None:
        os.environ["ALPHA_ENABLED_AGENTS"] = args.enabled
    if args.loglevel:
        os.environ["LOGLEVEL"] = args.loglevel.upper()


def main() -> None:
    """Parse CLI arguments and run the orchestrator indefinitely."""
    args = _parse_args()
    if args.version:
        print(__version__)
        return
    if args.preflight:
        _preflight()
        return
    _apply_env(args)
    Orchestrator().run_forever()


if __name__ == "__main__":
    main()
