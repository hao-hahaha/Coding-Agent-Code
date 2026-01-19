"""Environment-driven configuration shared across components."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, cast

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


@dataclass(slots=True)
class Settings:
    """Environment-driven configuration."""

    openai_api_key: str | None = get_secret("OPENAI_API_KEY")
    offline: bool = os.getenv("AGI_INSIGHT_OFFLINE", "0") == "1"
    bus_port: int = _env_int("AGI_INSIGHT_BUS_PORT", 6006)
    ledger_path: str = os.getenv("AGI_INSIGHT_LEDGER_PATH", "./ledger/audit.db")

    def __post_init__(self) -> None:
        if not self.openai_api_key:
            _log.warning("OPENAI_API_KEY missing – offline mode enabled")
            self.offline = True


CFG = Settings()
