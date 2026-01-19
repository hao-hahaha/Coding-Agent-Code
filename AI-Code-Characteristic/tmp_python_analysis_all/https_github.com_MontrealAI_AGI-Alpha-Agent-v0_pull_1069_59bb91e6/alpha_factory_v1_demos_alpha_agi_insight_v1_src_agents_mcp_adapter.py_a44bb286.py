# SPDX-License-Identifier: Apache-2.0
"""Adapter for the Anthropic Model Context Protocol client."""
from __future__ import annotations


class MCPAdapter:
    """Lightweight wrapper for :mod:`mcp` to avoid hard dependency."""

    def __init__(self) -> None:
        import importlib

        mcp = importlib.import_module("mcp")
        self._group = mcp.ClientSessionGroup()

    @classmethod
    def is_available(cls) -> bool:
        try:
            import importlib

            importlib.import_module("mcp")
            return True
        except Exception:
            return False

    def heartbeat(self) -> None:
        """Simple read of internal state to ensure the object works."""
        _ = len(self._group.sessions)

    async def invoke_tool(self, name: str, args: dict[str, object] | None = None) -> object:
        """Invoke a tool by name using :class:`mcp.ClientSessionGroup`."""
        args = args or {}
        return await self._group.call_tool(name, args)
