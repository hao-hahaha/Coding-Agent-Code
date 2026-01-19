"""Command line launcher for Alpha‑Factory v1."""

import os
import argparse
from pathlib import Path
from .scripts.preflight import main as preflight_main
from . import __version__


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Alpha-Factory launcher")
    ap.add_argument("--dev", action="store_true", help="Enable dev mode")
    ap.add_argument("--env-file", help="Load environment variables from file")
    ap.add_argument("--preflight", action="store_true", help="Run environment checks and exit")
    ap.add_argument("--port", type=int, help="REST API port")
    ap.add_argument("--metrics-port", type=int, help="Prometheus metrics port")
    ap.add_argument("--a2a-port", type=int, help="A2A gRPC port")
    ap.add_argument("--enabled", help="Comma separated list of enabled agents")
    ap.add_argument("--loglevel", default="INFO", help="Log level")
    ap.add_argument("--version", action="store_true", help="Print version and exit")
    return ap.parse_args()


def apply_env(args: argparse.Namespace) -> None:
    env_file = args.env_file
    if env_file is None and Path(".env").is_file():
        env_file = ".env"
    if env_file:
        for line in Path(env_file).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    if args.dev:
        os.environ["DEV_MODE"] = "true"
    if args.port is not None:
        os.environ["PORT"] = str(args.port)
    if args.metrics_port is not None:
        os.environ["METRICS_PORT"] = str(args.metrics_port)
    if args.a2a_port is not None:
        os.environ["A2A_PORT"] = str(args.a2a_port)
    if args.enabled is not None:
        os.environ["ALPHA_ENABLED_AGENTS"] = args.enabled
    if args.loglevel:
        os.environ["LOGLEVEL"] = args.loglevel.upper()


def run() -> None:
    args = parse_args()
    if args.version:
        print(__version__)
        return
    if args.preflight:
        preflight_main()
        return
    apply_env(args)
    from .backend.orchestrator import Orchestrator
    Orchestrator().run_forever()


if __name__ == "__main__":
    run()
