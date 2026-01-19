"""safety_compliance_reward.py – Alpha‑Factory v1 👁️✨
================================================================
Reward backend that *rewards policy compliance* and *penalises safety
violations*, encouraging the agent to self‑correct whenever possible.

Expected `result` payload (emitted by the Macro‑Sentinel layer or any policy
engine):

    {
        "request_id"   : "abc‑123",      # stable unique ID per request
        "violation"    : false,          # bool – any violation after tools?
        "severity"     : 0,              # 0‑10  (optional if `violation`=False)
        "autocorrected": true,           # did the agent self‑correct in‑flight?
        "violation_type": "harassment",  # optional taxonomy label
        "timestamp"    : "2025-04-22T15:02:33.507Z"
    }

Scoring ‒ clipped to [‑2.0, 1.0]
---------------------------------
+ **No violation** ..................... +1.0

+ **Self‑corrected** .................... +0.4 × (1 – severity/10)

+ **Unhandled violation** ............... −1.0 × (1 + severity/10)
                                           (max −2.0)

Implementation details
----------------------
* Zero external dependencies (std‑lib only)
* Thread‑safe via a `threading.Lock`
* Duplicate `request_id`s are ignored (idempotent)
* Unknown / malformed payload → neutral reward 0.0
* Apache‑2.0 License

© 2025 Montreal.AI
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Set

__all__ = ["reward"]

_log = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Internal state                                                             #
# --------------------------------------------------------------------------- #
_seen_request_ids: Set[str] = set()
_lock = threading.Lock()

# --------------------------------------------------------------------------- #
#  Helpers                                                                    #
# --------------------------------------------------------------------------- #
def _to_bool(value: Any) -> bool:
    """Return best‑effort bool conversion (`'true'`, `'1'` → True)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return False


def _clip(val: float, lo: float = -2.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


# --------------------------------------------------------------------------- #
#  Public API                                                                 #
# --------------------------------------------------------------------------- #
def reward(state: Any, action: Any, result: Any) -> float:  # noqa: D401
    """Compute safety‑compliance reward in the range [‑2.0, 1.0]."""
    if not isinstance(result, dict):
        _log.debug("safety_compliance_reward: result is not a dict → 0.0")
        return 0.0

    # ------------------------------------------------------------------ #
    #  Idempotency guard                                                  #
    # ------------------------------------------------------------------ #
    req_id = str(result.get("request_id", "")).strip()
    with _lock:
        if req_id and req_id in _seen_request_ids:
            _log.debug("duplicate request_id %s → 0.0", req_id)
            return 0.0
        if req_id:
            _seen_request_ids.add(req_id)

    # ------------------------------------------------------------------ #
    #  Extract & sanitise fields                                         #
    # ------------------------------------------------------------------ #
    violation    = _to_bool(result.get("violation", False))
    autocorrect  = _to_bool(result.get("autocorrected", False))

    # Severity: float ∈ [0,10], infer 0 if missing / bad
    try:
        severity = float(result.get("severity", 0.0))
    except Exception:  # noqa: BLE001
        severity = 0.0
    severity = max(0.0, min(10.0, severity))

    # ------------------------------------------------------------------ #
    #  Score                                                              #
    # ------------------------------------------------------------------ #
    if not violation:
        return 1.0

    if autocorrect:
        # Positive — encourage self‑regulation, but discount by severity
        return _clip(0.4 * (1.0 - severity / 10.0))

    # Negative penalty; grows w/ severity (max −2.0)
    return _clip(-1.0 * (1.0 + severity / 10.0))
