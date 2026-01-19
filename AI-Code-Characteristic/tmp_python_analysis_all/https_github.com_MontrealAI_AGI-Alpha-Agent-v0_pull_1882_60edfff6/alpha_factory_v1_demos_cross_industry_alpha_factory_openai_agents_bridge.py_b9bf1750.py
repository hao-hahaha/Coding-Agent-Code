# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env python3
# NOTE: This demo is a research prototype and does not implement real AGI.
"""OpenAI Agents SDK bridge for the cross-industry Alpha-Factory demo."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

from .cross_alpha_discovery_stub import SAMPLE_ALPHA, discover_alpha, _ledger_path

try:
    from openai_agents import Agent, AgentRuntime, Tool
except ModuleNotFoundError as exc:  # pragma: no cover - optional dep
    raise SystemExit(
        "openai-agents package is missing. Install with `pip install openai-agents`"
    ) from exc


def _read_log(limit: int) -> List[Dict[str, str]]:
    path = _ledger_path(None)
    try:
        data = json.loads(Path(path).read_text())
        if isinstance(data, dict):
            data = [data]
        return data[-limit:]
    except (
        FileNotFoundError,
        PermissionError,
        json.JSONDecodeError,
    ):  # pragma: no cover - missing or invalid log
        return []


@Tool(name="list_samples", description="List bundled sample opportunities")
async def list_samples() -> List[Dict[str, str]]:
    return SAMPLE_ALPHA


@Tool(name="discover_alpha", description="Generate new opportunities")
async def discover(num: int = 1) -> List[Dict[str, str]]:
    return discover_alpha(num=num)


@Tool(name="recent_log", description="Return recently logged opportunities")
async def recent_log(limit: int = 5) -> List[Dict[str, str]]:
    return _read_log(limit)


class CrossIndustryAgent(Agent):
    """Agent exposing cross-industry discovery tools."""

    name = "cross_industry_helper"
    tools = [list_samples, discover, recent_log]

    async def policy(self, obs, ctx):  # type: ignore[override]
        if isinstance(obs, dict):
            action = obs.get("action")
            if action == "discover":
                return await self.tools.discover(obs.get("num", 1))
            if action == "recent":
                return await self.tools.recent_log(obs.get("limit", 5))
        return await self.tools.list_samples()


def main() -> None:
    runtime = AgentRuntime(api_key=None)
    agent = CrossIndustryAgent()
    runtime.register(agent)
    try:
        from alpha_factory_v1.backend.adk_bridge import auto_register, maybe_launch

        auto_register([agent])
        maybe_launch()
    except Exception as exc:  # pragma: no cover - ADK optional
        logger.warning(f"ADK bridge unavailable: {exc}")

    logger.info("Registered CrossIndustryAgent with runtime")
    runtime.run()


if __name__ == "__main__":  # pragma: no cover
    main()
