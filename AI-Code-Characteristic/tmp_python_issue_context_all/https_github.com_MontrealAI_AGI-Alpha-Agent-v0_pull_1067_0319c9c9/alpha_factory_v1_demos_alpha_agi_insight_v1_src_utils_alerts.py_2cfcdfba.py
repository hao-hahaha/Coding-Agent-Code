# SPDX-License-Identifier: Apache-2.0
"""Simple webhook alerts for restarts and failures."""

from __future__ import annotations

import logging
import os

try:
    import af_requests as requests
except Exception:  # pragma: no cover - optional real requests
    import requests  # type: ignore

__all__ = ["send_alert"]

_log = logging.getLogger(__name__)


def send_alert(message: str, url: str | None = None) -> None:
    """Post *message* to ``url`` or ``ALERT_WEBHOOK_URL`` if set."""

    hook = url or os.getenv("ALERT_WEBHOOK_URL")
    if not hook:
        return

    payload = {"content": message}
    if "slack.com" in hook:
        payload = {"text": message}

    try:
        resp = requests.post(hook, json=payload, timeout=5)
        if not 200 <= resp.status_code <= 299:
            _log.warning("alert failed with status %s", resp.status_code)
    except Exception as exc:  # pragma: no cover - network errors
        _log.warning("alert failed: %s", exc)
