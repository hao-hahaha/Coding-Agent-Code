"""Environment-driven configuration shared across components."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional, cast

from alpha_factory_v1.utils.env import _load_env_file

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_log = logging.getLogger(__name__)


def _load_dotenv(path: str = ".env") -> None:
    if Path(path).is_file():
        for k, v in _load_env_file(path).items():
            os.environ.setdefault(k, v)




def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return ``name`` from the configured secret backend or environment.

    The backend is selected via ``AGI_INSIGHT_SECRET_BACKEND``. Supported values
    are ``vault``, ``aws`` and ``gcp``. When unset or empty, the environment
    variable ``name`` is returned. Any backend error logs a warning and falls
    back to ``os.getenv(name, default)``.
    """
    backend = os.getenv("AGI_INSIGHT_SECRET_BACKEND", "").lower()
    if not backend or backend == "env":
        return os.getenv(name, default)

    if backend == "vault":
        try:  # pragma: no cover - optional deps
            import importlib

            hvac = importlib.import_module("hvac")

            addr = os.environ["VAULT_ADDR"]
            token = os.environ["VAULT_TOKEN"]
            secret_path = os.getenv(f"{name}_PATH", name)
            client = hvac.Client(url=addr, token=token)
            data = client.secrets.kv.read_secret_version(path=secret_path)
            return cast(Optional[str], data["data"]["data"].get(name, default))
        except Exception as exc:  # noqa: BLE001
            _log.warning("Vault secret '%s' failed: %s", name, exc)
            return os.getenv(name, default)

    if backend == "aws":
        try:  # pragma: no cover - optional deps
            import importlib

            boto3 = importlib.import_module("boto3")

            region = os.getenv("AWS_REGION", "us-east-1")
            secret_id = os.getenv(f"{name}_SECRET_ID", name)
            client = boto3.client("secretsmanager", region_name=region)
            resp = client.get_secret_value(SecretId=secret_id)
            return cast(Optional[str], resp.get("SecretString", default))
        except Exception as exc:  # noqa: BLE001
            _log.warning("AWS secret '%s' failed: %s", name, exc)
            return os.getenv(name, default)

    if backend == "gcp":
        try:  # pragma: no cover - optional deps
            import importlib

            secretmanager = importlib.import_module("google.cloud.secretmanager")

            project = os.environ["GCP_PROJECT_ID"]
            secret_id = os.getenv(f"{name}_SECRET_ID", name)
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{project}/secrets/{secret_id}/versions/latest"
            resp = client.access_secret_version(name=secret_name)
            return cast(str, resp.payload.data.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            _log.warning("GCP secret '%s' failed: %s", name, exc)
            return os.getenv(name, default)

    _log.warning("Unknown secret backend '%s'", backend)
    return os.getenv(name, default)


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


def init_config(env_file: str = ".env") -> None:
    """Load environment variables and refresh :data:`CFG`."""

    _load_dotenv(env_file)
    _prefetch_vault()
    global CFG
    CFG = Settings()




class Settings(BaseSettings):
    """Environment-driven configuration."""

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    offline: bool = Field(default=False, alias="AGI_INSIGHT_OFFLINE")
    bus_port: int = Field(default=6006, alias="AGI_INSIGHT_BUS_PORT")
    ledger_path: str = Field(default="./ledger/audit.db", alias="AGI_INSIGHT_LEDGER_PATH")

    model_config: SettingsConfigDict = {
        "env_file": ".env",
        "extra": "ignore",
        "populate_by_name": True,
        "env_prefix": "",
    }

    def __init__(self, **data: Any) -> None:  # pragma: no cover - exercised in tests
        super().__init__(**data)
        if not self.openai_api_key:
            self.openai_api_key = get_secret("OPENAI_API_KEY")
        if not self.openai_api_key:
            _log.warning("OPENAI_API_KEY missing – offline mode enabled")
            self.offline = True

    def __repr__(self) -> str:  # pragma: no cover - trivial
        data = self.model_dump()
        for k in tuple(data):
            if any(s in k.lower() for s in ("token", "key", "password")) and data[k]:
                data[k] = "***"
        return f"Settings({data})"


CFG = Settings()
