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

# allow running this script directly from its folder
SCRIPT_DIR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - offline shim
    from alpha_factory_v1 import requests  # type: ignore


# ---------------------------------------------------------------------------
# Lazy dependency bootstrap
# ---------------------------------------------------------------------------
def _require_openai_agents() -> bool:
    """Ensure the ``openai_agents`` package is available.

    Attempts an automatic install via :mod:`check_env` when the package is
    missing so the bridge remains usable in fresh environments or Colab
    runtimes.  Returns ``True`` when the package can be imported, ``False``
    otherwise without raising ``SystemExit``.  This allows the demo to run in
    fully offline environments where installation may fail.
    """

    try:  # soft dependency
        import openai_agents  # type: ignore

        return True
    except ModuleNotFoundError:  # pragma: no cover - optional dep
        try:
            import check_env

            print("ℹ️  openai_agents missing – attempting auto-install…")
            check_env.main(["--auto-install"])
            import openai_agents  # type: ignore  # noqa: F401

            return True
        except Exception as exc:  # pragma: no cover - install failed
            sys.stderr.write(f"\n⚠️  openai_agents unavailable: {exc}\n")
            sys.stderr.write("   Continuing without OpenAI Agents bridge.\n")
            return False


_OPENAI_AGENTS_AVAILABLE = _require_openai_agents()
if _OPENAI_AGENTS_AVAILABLE:
    from openai_agents import Agent, AgentRuntime, Tool  # type: ignore
else:  # pragma: no cover - offline fallback
    Agent = object  # type: ignore

    class AgentRuntime:  # type: ignore
        def __init__(self, *a, **kw) -> None:
            pass

        def register(self, *a, **kw) -> None:
            pass

        def run(self) -> None:
            print("OpenAI Agents bridge disabled.")

    def Tool(*_args, **_kw):  # type: ignore
        def _decorator(func):
            return func

        return _decorator


try:
    # Optional ADK bridge
    from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch

    ADK_AVAILABLE = True
except ImportError:  # pragma: no cover - ADK not installed
    ADK_AVAILABLE = False

HOST = os.getenv("BUSINESS_HOST", "http://localhost:8000")
AGENT_PORT = int(os.getenv("AGENTS_RUNTIME_PORT", "5001"))


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
        "--port",
        type=int,
        default=AGENT_PORT,
        help=f"Port for the Agents runtime (default: {AGENT_PORT})",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Do not wait for orchestrator readiness",
    )
    parser.add_argument(
        "--wait-secs",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="How long to wait for orchestrator health check (default: 5)",
    )
    parser.add_argument(
        "--open-ui",
        action="store_true",
        help="Open the Agents runtime URL in the default browser",
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


@Tool(name="trigger_risk", description="Trigger the AlphaRiskAgent")
async def trigger_risk() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_risk/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_risk queued"


@Tool(name="trigger_compliance", description="Trigger the AlphaComplianceAgent")
async def trigger_compliance() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_compliance/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_compliance queued"


@Tool(name="trigger_portfolio", description="Trigger the AlphaPortfolioAgent")
async def trigger_portfolio() -> str:
    resp = requests.post(f"{HOST}/agent/alpha_portfolio/trigger", timeout=5)
    resp.raise_for_status()
    return "alpha_portfolio queued"


@Tool(name="check_health", description="Return orchestrator health status")
async def check_health() -> str:
    """Check orchestrator /healthz endpoint."""
    resp = requests.get(f"{HOST}/healthz", timeout=5)
    resp.raise_for_status()
    return resp.text


@Tool(
    name="submit_job",
    description="Submit a custom alpha job JSON to the orchestrator",
)
async def submit_job(job: dict) -> str:
    """Post a JSON job definition to the orchestrator.

    The dictionary must include an ``agent`` field specifying the target
    agent name. Additional fields are forwarded verbatim.
    """
    agent = job.get("agent")
    if not agent:
        raise ValueError("'agent' field required in job spec")
    resp = requests.post(
        f"{HOST}/agent/{agent}/trigger",
        json=job,
        timeout=5,
    )
    resp.raise_for_status()
    return f"job for {agent} queued"


@Tool(
    name="recent_alpha",
    description="Return recently discovered alpha opportunities",
)
async def recent_alpha(limit: int = 5) -> list[str]:
    """Fetch the latest alpha items from the orchestrator memory."""
    resp = requests.get(
        f"{HOST}/memory/alpha_opportunity/recent",
        params={"n": limit},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


@Tool(
    name="search_memory",
    description="Search orchestrator memory for a text query",
)
async def search_memory(query: str, limit: int = 5) -> list[str]:
    """Query the orchestrator memory vector store."""
    resp = requests.get(
        f"{HOST}/memory/search",
        params={"q": query, "k": limit},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


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
    """Tiny agent exposing orchestrator helper tools.

    The helper surfaces a curated set of REST endpoints via the
    OpenAI Agents runtime and optional ADK gateway.  It also supports
    vector memory search for quick retrieval of stored alpha.
    """

    name = "business_helper"
    tools = [
        list_agents,
        trigger_discovery,
        trigger_opportunity,
        trigger_execution,
        trigger_risk,
        trigger_compliance,
        trigger_portfolio,
        check_health,
        recent_alpha,
        search_memory,
        submit_job,
    ]

    async def policy(self, obs, ctx):  # type: ignore[override]
        if isinstance(obs, dict):
            if obs.get("action") == "discover":
                return await self.tools.trigger_discovery()
            elif obs.get("action") == "opportunity":
                return await self.tools.trigger_opportunity()
            elif obs.get("action") == "execute":
                return await self.tools.trigger_execution()
            elif obs.get("action") == "risk":
                return await self.tools.trigger_risk()
            elif obs.get("action") == "compliance":
                return await self.tools.trigger_compliance()
            elif obs.get("action") == "portfolio":
                return await self.tools.trigger_portfolio()
            elif obs.get("action") == "health":
                return await self.tools.check_health()
            elif obs.get("action") == "recent_alpha":
                return await self.tools.recent_alpha()
            elif obs.get("action") == "search_memory":
                query = obs.get("query", "")
                limit = int(obs.get("limit", 5))
                return await self.tools.search_memory(query, limit)
            elif obs.get("action") == "submit_job":
                job = obs.get("job", {})
                return await self.tools.submit_job(job)
        return await self.tools.list_agents()


def main() -> None:
    if not _OPENAI_AGENTS_AVAILABLE:
        print("OpenAI Agents SDK not available; bridge inactive.")
        return

    args = _parse_args()
    global HOST
    HOST = args.host
    api_key = os.getenv("OPENAI_API_KEY") or None
    if not args.no_wait:
        try:
            wait_ready(HOST, timeout=args.wait_secs)
        except RuntimeError as exc:
            sys.stderr.write(f"\n⚠️  {exc}\n")
            if api_key is None:
                sys.stderr.write("   continuing in offline mode...\n")
            else:
                sys.exit(1)
    runtime = AgentRuntime(api_key=api_key, port=args.port)
    agent = BusinessAgent()
    runtime.register(agent)
    print(f"Registered BusinessAgent -> {HOST} [port {args.port}]")
    if args.open_ui:
        url = f"http://localhost:{args.port}/v1/agents"
        try:
            import webbrowser

            webbrowser.open(url, new=1)
        except webbrowser.Error:
            print(f"Open {url} to access the Agents runtime")

    if ADK_AVAILABLE:
        auto_register([agent])
        maybe_launch()
        print("BusinessAgent exposed via ADK gateway")

    runtime.run()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
