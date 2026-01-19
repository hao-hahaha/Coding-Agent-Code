"""Configuration helpers for the α‑AGI Insight demo."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(slots=True)
class Settings:
    """Environment-driven configuration."""

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    offline: bool = os.getenv("AGI_INSIGHT_OFFLINE", "0") == "1"
    bus_port: int = _env_int("AGI_INSIGHT_BUS_PORT", 6006)
    ledger_path: str = os.getenv("AGI_INSIGHT_LEDGER_PATH", "./ledger/audit.db")
