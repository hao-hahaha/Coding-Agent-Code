# SPDX-License-Identifier: Apache-2.0
"""Lightweight helpers for evaluating OPA policies."""
from __future__ import annotations

import re
from pathlib import Path


_POLICY_DIR = Path(__file__).resolve().parents[2] / "policies"


def _load_banned_hosts() -> set[str]:
    policy_path = _POLICY_DIR / "deny_finance.rego"
    try:
        text = policy_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return set()
    m = re.search(r"banned_hosts\s*=\s*{([^}]*)}", text, re.DOTALL)
    if not m:
        return set()
    hosts = [h.strip().strip('"') for h in m.group(1).split(',') if h.strip()]
    return set(hosts)


_BANNED_HOSTS = _load_banned_hosts()


def violates_finance_policy(code: str) -> bool:
    """Return ``True`` if ``code`` references a banned finance API host."""
    for host in _BANNED_HOSTS:
        if host in code:
            return True
    return False
