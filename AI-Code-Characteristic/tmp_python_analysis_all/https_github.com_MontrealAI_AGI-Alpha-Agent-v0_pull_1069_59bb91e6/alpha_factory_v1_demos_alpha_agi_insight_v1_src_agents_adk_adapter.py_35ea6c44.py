# SPDX-License-Identifier: Apache-2.0
"""Lightweight wrapper around the optional Google ADK client."""
from __future__ import annotations


class ADKAdapter:
    """Minimal facade for the :mod:`adk` package."""

    def __init__(self) -> None:
        import importlib

        try:
            adk = importlib.import_module("adk")
        except ModuleNotFoundError:  # pragma: no cover - fallback name
            adk = importlib.import_module("google.adk")
        if not hasattr(adk, "Client"):
            raise ImportError("adk.Client missing")
        self._client = adk.Client()

    @classmethod
    def is_available(cls) -> bool:
        try:
            import importlib

            mod = importlib.import_module("adk")
        except Exception:
            try:
                mod = importlib.import_module("google.adk")
            except Exception:
                return False
        return hasattr(mod, "Client")

    def heartbeat(self) -> None:
        """Invoke a trivial call if available."""
        ping = getattr(self._client, "ping", None)
        if callable(ping):
            ping()

    def list_packages(self) -> list[str]:
        """Return remote package names from the ADK mesh."""
        list_fn = getattr(self._client, "list_remote_packages", None)
        if not callable(list_fn):
            raise AttributeError("list_remote_packages not available")
        return [pkg.name for pkg in list_fn()]
