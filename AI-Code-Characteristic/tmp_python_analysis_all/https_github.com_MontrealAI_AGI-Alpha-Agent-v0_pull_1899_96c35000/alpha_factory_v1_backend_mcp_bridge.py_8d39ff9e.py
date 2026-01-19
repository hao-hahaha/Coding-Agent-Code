# SPDX-License-Identifier: Apache-2.0
"""
alpha_factory_v1.backend.mcp_bridge
===================================

Ultra-thin helper around Anthropic’s *Model-Context-Protocol* (MCP).

Only one primitive is provided:

``store(messages)`` – Best-effort persistence of raw chat messages.

If ``MCP_ENDPOINT`` is undefined the module becomes a silent no-op.
``MCP_TIMEOUT_SEC`` controls the network timeout (default ``10``).

Enable by exporting, e.g.::

    MCP_ENDPOINT="http://mcp.service.local:8980/v1"
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import List, TypedDict

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover - optional dep
    httpx = None

from .logger import get_logger


__all__ = ["store", "store_sync"]

_LOG = get_logger("alpha_factory.mcp")

_ENDPOINT = os.getenv("MCP_ENDPOINT")          # http://host:port/v1
_TIMEOUT = float(os.getenv("MCP_TIMEOUT_SEC", 10))


class ChatMessage(TypedDict):
    """OpenAI-style chat message."""

    role: str
    content: str


async def store(messages: List[ChatMessage]) -> None:
    """
    Asynchronously push *raw* chat messages to an MCP server.

    The call is fire-and-forget and **never** raises – MCP is non-critical.
    """
    if not _ENDPOINT:
        return

    if httpx is None:
        _LOG.debug("MCP disabled – httpx missing")
        return

    payload = {"messages": messages, "timestamp": time.time()}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            await client.post(f"{_ENDPOINT}/context", json=payload)
    except Exception:  # noqa: BLE001
        # Best-effort only → log at debug level if the caller configured logging
        _LOG.debug("MCP push failed – continuing without persistence", exc_info=True)


def store_sync(messages: List[ChatMessage]) -> None:
    """
    Synchronous convenience wrapper for rare call-sites that are outside
    an event-loop (e.g. CLI utilities or unit tests).
    """
    asyncio.run(store(messages))

