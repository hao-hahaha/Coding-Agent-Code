# SPDX-License-Identifier: Apache-2.0
"""Lightweight wrapper around the optional Google ADK client."""
from __future__ import annotations


class ADKAdapter:
    """Minimal facade for the :mod:`adk` package."""

    def __init__(self) -> None:
        import importlib

        adk = importlib.import_module("adk")
        self._client = adk.Client()

    @classmethod
    def is_available(cls) -> bool:
        try:
            import importlib

            importlib.import_module("adk")
            return True
        except Exception:
            return False

    def heartbeat(self) -> None:
        """Invoke a trivial call if available."""
        ping = getattr(self._client, "ping", None)
        if callable(ping):
            ping()
