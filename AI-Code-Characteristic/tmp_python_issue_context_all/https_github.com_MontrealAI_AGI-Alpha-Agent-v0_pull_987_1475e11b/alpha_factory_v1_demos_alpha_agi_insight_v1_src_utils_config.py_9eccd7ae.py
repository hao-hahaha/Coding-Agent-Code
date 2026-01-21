# SPDX-License-Identifier: Apache-2.0
"""Environment driven settings used by the agents and interfaces.

The :class:`Settings` dataclass gathers options from ``.env`` files and
environment variables. ``CFG`` is the default instance consumed throughout
the demo.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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


def _prefetch_vault() -> None:
    """Populate environment secrets from HashiCorp Vault if configured."""
    if "VAULT_ADDR" in os.environ:
        try:  # pragma: no cover - optional dependency
            import importlib

            hvac = importlib.import_module("hvac")

            addr = os.environ["VAULT_ADDR"]
            token = os.getenv("VAULT_TOKEN")
            secret_path = os.getenv("OPENAI_API_KEY_PATH", "OPENAI_API_KEY")
            client = hvac.Client(url=addr, token=token)
            data = client.secrets.kv.read_secret_version(path=secret_path)
            value = data["data"]["data"].get("OPENAI_API_KEY")
            if value:
                os.environ["OPENAI_API_KEY"] = value
        except Exception as exc:  # noqa: BLE001
            _log.warning("Vault lookup failed: %s", exc)


class Settings(BaseSettings):
    """Environment-driven configuration."""

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    offline: bool = Field(default=False, alias="AGI_INSIGHT_OFFLINE")
    bus_port: int = Field(default=6006, alias="AGI_INSIGHT_BUS_PORT")
    ledger_path: str = Field(default="./ledger/audit.db", alias="AGI_INSIGHT_LEDGER_PATH")
    memory_path: Optional[str] = Field(default=None, alias="AGI_INSIGHT_MEMORY_PATH")
    broker_url: Optional[str] = Field(default=None, alias="AGI_INSIGHT_BROKER_URL")
    bus_token: Optional[str] = Field(default=None, alias="AGI_INSIGHT_BUS_TOKEN")
    bus_cert: Optional[str] = Field(default=None, alias="AGI_INSIGHT_BUS_CERT")
    bus_key: Optional[str] = Field(default=None, alias="AGI_INSIGHT_BUS_KEY")
    allow_insecure: bool = Field(default=False, alias="AGI_INSIGHT_ALLOW_INSECURE")
    broadcast: bool = Field(default=True, alias="AGI_INSIGHT_BROADCAST")
    solana_rpc_url: str = Field(default="https://api.testnet.solana.com", alias="AGI_INSIGHT_SOLANA_URL")
    solana_wallet: Optional[str] = Field(default=None, alias="AGI_INSIGHT_SOLANA_WALLET")
    solana_wallet_file: Optional[str] = Field(default=None, alias="AGI_INSIGHT_SOLANA_WALLET_FILE")
    model_name: str = Field(default="gpt-4o-mini", alias="AGI_MODEL_NAME")
    temperature: float = Field(default=0.2, alias="AGI_TEMPERATURE")
    context_window: int = Field(default=8192, alias="AGI_CONTEXT_WINDOW")
    json_logs: bool = Field(default=False, alias="AGI_INSIGHT_JSON_LOGS")
    db_type: str = Field(default="sqlite", alias="AGI_INSIGHT_DB")

    model_config: SettingsConfigDict = {
        "env_file": ".env",
        "extra": "ignore",
        "populate_by_name": True,
        "env_prefix": "",
    }

    def __init__(self, **data: Any) -> None:  # pragma: no cover - exercised in tests
        super().__init__(**data)
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

    def __repr__(self) -> str:  # pragma: no cover - trivial
        data = self.model_dump()
        for k in tuple(data):
            if any(s in k.lower() for s in ("token", "key", "password")) and data[k]:
                data[k] = "***"
        return f"Settings({data})"

_prefetch_vault()

CFG = Settings()
