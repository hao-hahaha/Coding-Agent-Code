#!/usr/bin/env python3
"""OpenAI Agents SDK bridge for the alpha_agi_business_v1 demo.

This utility registers a small helper agent that interacts with the
local orchestrator. It works offline when no API key is configured.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import requests

# ---------------------------------------------------------------------------
# Lazy dependency bootstrap
# ---------------------------------------------------------------------------
def _require_openai_agents() -> None:
    """Ensure the ``openai_agents`` package is available.

    Attempts an automatic install via :mod:`check_env` when the package is
    missing so the bridge remains usable in fresh environments or Colab
    runtimes. Any installation errors are surfaced to the user.
    """

    try:  # soft dependency
        import openai_agents  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - optional dep
        try:
            import check_env

            print("ℹ️  openai_agents missing – attempting auto-install…")
            check_env.main(["--auto-install"])
        except Exception as exc:  # pragma: no cover - install failed
            sys.stderr.write(
                f"\n❌  openai_agents not installed and auto-install failed: {exc}\n"
            )
            sys.stderr.write("   Install manually with 'pip install openai-agents'\n")
            sys.exit(1)
        try:
            import openai_agents  # type: ignore  # noqa: F401
        except ModuleNotFoundError:
            sys.stderr.write(
                "\n❌  openai_agents still missing after auto-install.\n"
            )
            sys.stderr.write("   Install manually with 'pip install openai-agents'\n")
            sys.exit(1)


_require_openai_agents()
from openai_agents import Agent, AgentRuntime, Tool  # type: ignore

try:
    # Optional ADK bridge
    from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch
    ADK_AVAILABLE = True
except ImportError:  # pragma: no cover - ADK not installed
    ADK_AVAILABLE = False

HOST = os.getenv("BUSINESS_HOST", "http://localhost:8000")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expose alpha_agi_business_v1 via OpenAI Agents runtime"
    )
    parser.add_argument(
        "--host",
        default=HOST,
        help="Orchestrator host URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Do not wait for orchestrator readiness",
    )
    return parser.parse_args(argv)


@Tool(name="list_agents", description="List active orchestrator agents")
async def list_agents() -> list[str]:
    resp = requests.get(f"{HOST}/agents", timeout=5)
    resp.raise_for_status()
    return resp.json()


@Tool(name="trigger_discovery", description="Trigger the AlphaDiscoveryAgent")
async def trigger_discovery() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_discovery/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_discovery queued"


@Tool(name="trigger_opportunity", description="Trigger the AlphaOpportunityAgent")
async def trigger_opportunity() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_opportunity/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_opportunity queued"


@Tool(name="trigger_execution", description="Trigger the AlphaExecutionAgent")
async def trigger_execution() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_execution/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_execution queued"


def wait_ready(url: str, timeout: float = 5.0) -> None:
    """Block until the orchestrator healthcheck responds or timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if requests.get(f"{url}/healthz", timeout=1).status_code == 200:
                return
        except Exception:
            time.sleep(0.2)
    raise RuntimeError(f"Orchestrator not reachable at {url}")


class BusinessAgent(Agent):
    """Tiny agent exposing orchestrator helper tools."""

    name = "business_helper"
    tools = [list_agents, trigger_discovery, trigger_opportunity, trigger_execution]

    async def policy(self, obs, ctx):  # type: ignore[override]
        if isinstance(obs, dict):
            if obs.get("action") == "discover":
                return await self.tools.trigger_discovery()
            elif obs.get("action") == "opportunity":
                return await self.tools.trigger_opportunity()
            elif obs.get("action") == "execute":
                return await self.tools.trigger_execution()
        return await self.tools.list_agents()


def main() -> None:
    args = _parse_args()
    global HOST
    HOST = args.host
    api_key = os.getenv("OPENAI_API_KEY") or None
    if not args.no_wait:
        try:
            wait_ready(HOST)
        except RuntimeError as exc:
            sys.stderr.write(f"\n⚠️  {exc}\n")
            if api_key is None:
                sys.stderr.write("   continuing in offline mode...\n")
            else:
                sys.exit(1)
    runtime = AgentRuntime(api_key=api_key)
    agent = BusinessAgent()
    runtime.register(agent)
    print(f"Registered BusinessAgent -> {HOST}")

    if ADK_AVAILABLE:
        auto_register([agent])
        maybe_launch()
        print("BusinessAgent exposed via ADK gateway")

    runtime.run()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
