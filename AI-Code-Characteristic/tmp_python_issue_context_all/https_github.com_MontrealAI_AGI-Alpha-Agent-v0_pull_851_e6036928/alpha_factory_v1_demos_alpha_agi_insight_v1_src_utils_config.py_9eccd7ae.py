# SPDX-License-Identifier: Apache-2.0
"""Environment driven settings used by the agents and interfaces.

The :class:`Settings` dataclass gathers options from ``.env`` files and
environment variables. ``CFG`` is the default instance consumed throughout
the demo.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


_log = logging.getLogger(__name__)


def _load_env_file(path: str | os.PathLike[str]) -> Dict[str, str]:
    """Return key/value pairs from ``path``.

    Falls back to a minimal parser when :mod:`python_dotenv` is unavailable.
    """
    try:  # pragma: no cover - optional dependency
        from dotenv import dotenv_values

        return {k: v for k, v in dotenv_values(path).items() if v is not None}
    except Exception:  # noqa: BLE001 - any import/parsing error falls back
        pass

    data: Dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip().strip('"')
    return data


def _load_dotenv(path: str = ".env") -> None:
    if Path(path).is_file():
        for k, v in _load_env_file(path).items():
            os.environ.setdefault(k, v)


_load_dotenv()


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
    broker_url: str | None = os.getenv("AGI_INSIGHT_BROKER_URL")
    bus_token: str | None = os.getenv("AGI_INSIGHT_BUS_TOKEN")
    bus_cert: str | None = os.getenv("AGI_INSIGHT_BUS_CERT")
    bus_key: str | None = os.getenv("AGI_INSIGHT_BUS_KEY")
    broadcast: bool = os.getenv("AGI_INSIGHT_BROADCAST", "1") == "1"
    solana_rpc_url: str = os.getenv("AGI_INSIGHT_SOLANA_URL", "https://api.testnet.solana.com")
    solana_wallet: str | None = os.getenv("AGI_INSIGHT_SOLANA_WALLET")
    solana_wallet_file: str | None = os.getenv("AGI_INSIGHT_SOLANA_WALLET_FILE")

    def __post_init__(self) -> None:
        if not self.openai_api_key:
            _log.warning("OPENAI_API_KEY missing – offline mode enabled")
            self.offline = True
        if self.offline:
            self.broadcast = False
        if not self.solana_wallet and self.solana_wallet_file:
            try:
                self.solana_wallet = Path(self.solana_wallet_file).read_text(encoding="utf-8").strip()
            except Exception as exc:  # pragma: no cover - optional
                _log.warning("Failed to load wallet file %s: %s", self.solana_wallet_file, exc)


CFG = Settings()
