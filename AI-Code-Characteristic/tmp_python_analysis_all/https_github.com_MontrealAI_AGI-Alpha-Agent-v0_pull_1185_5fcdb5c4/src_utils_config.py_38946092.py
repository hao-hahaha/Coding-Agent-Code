# SPDX-License-Identifier: Apache-2.0
"""Environment-driven configuration shared across components."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional, cast

from alpha_factory_v1.utils.config_common import (
    SettingsBase,
    _load_dotenv,
    _prefetch_vault,
)

from pydantic import Field

_log = logging.getLogger(__name__)


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


def init_config(env_file: str = ".env") -> None:
    """Load environment variables and refresh :data:`CFG`."""

    _load_dotenv(env_file)
    _prefetch_vault()
    global CFG
    CFG = Settings()


class Settings(SettingsBase):
    """Environment-driven configuration."""

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    offline: bool = Field(default=False, alias="AGI_INSIGHT_OFFLINE")
    bus_port: int = Field(default=6006, alias="AGI_INSIGHT_BUS_PORT")
    ledger_path: str = Field(default="./ledger/audit.db", alias="AGI_INSIGHT_LEDGER_PATH")
    seed: Optional[int] = Field(default=None, alias="SEED")

    def __init__(self, **data: Any) -> None:  # pragma: no cover - exercised in tests
        super().__init__(**data)
        if not self.openai_api_key:
            self.openai_api_key = get_secret("OPENAI_API_KEY")
        if not self.openai_api_key:
            _log.warning("OPENAI_API_KEY missing – offline mode enabled")
            self.offline = True


CFG = Settings()
