
"""
habit_consistency_reward.py – Alpha‑Factory v1 👁️✨
==================================================

Reward backend that encourages **consistent repetition of beneficial habits**
(e.g. daily running, language study, meditation).

*Grounding*: The «grounded‑rewards» pillar from *The Era of Experience*
(Sutton & Silver, 2024) advocates directly measurable signals rather than
human‑authored heuristics.  Here we surface *temporal regularity* as an
experience‑grounded proxy for self‑discipline and healthy routine building.

---------------------------------------------------------------------------
Expected *result* payload
-------------------------
The orchestrator should forward an *observation* that contains **at least**:

    {
        "context": "<habit-key> … free‑form text …",
        "time":    "2025-04-22T07:12:03Z"   # ISO‑8601
    }

• The *habit‑key* is extracted as the first whitespace‑separated token in
  ``context`` (lower‑cased, unicode‑normalised).

• ``time`` may include timezone / 'Z' suffix — it is parsed with
  ``datetime.fromisoformat`` as best effort.

---------------------------------------------------------------------------
Scoring
-------
1. First ever sighting of a habit: **+0.25**  
   _Rationale_: seed exploration without overweighting cold‑start.

2. Subsequent occurrences compute the elapsed hours ``Δ`` since *the SAME*
   habit last appeared:

    | Δ hours | Reward | Intuition                |
    |---------|--------|--------------------------|
    | ≤ 36    | +1.0   | daily / highly consistent|
    | ≤ 72    | +0.5   | every other day          |
    | ≤ 168   | +0.2   | weekly touch‑point       |
    |  > 168  |  0.0   | inconsistency penalty    |

---------------------------------------------------------------------------
Implementation notes
--------------------
• **Thread‑safe**: a per‑process memory dictionary protected by a Lock.  
• **Stateless config**: tweak thresholds via module‑level constants.  
• **Zero deps**: std‑lib only — works offline, inside minimal containers.

© 2025 Montreal.AI – Apache-2.0 License
"""

from __future__ import annotations

import datetime as _dt
import logging as _lg
import threading as _th
import unicodedata as _ud
from typing import Any, Dict, Final

__all__ = ["reward"]

_LOG: Final = _lg.getLogger(__name__)

# ─────────────────────────────── config ──────────────────────────────────────
FIRST_SIGHT_REWARD:   Final[float] = 0.25
DELTA_THRESHOLDS:     Final[Dict[float, float]] = {
    36.0: 1.0,        # ≤ 1.5 days
    72.0: 0.5,        # ≤ 3   days
    168.0: 0.2,       # ≤ 1   week
}
# Anything above max(DELTA_THRESHOLDS) → 0.0

_ISO_FMT_COMPACT: Final[str] = "%Y-%m-%dT%H:%M:%S"

# ─────────────────────────── internal state ──────────────────────────────────
_last_seen: Dict[str, _dt.datetime] = {}
_lock = _th.Lock()

# ─────────────────────────── helper functions ────────────────────────────────
def _normalise_habit(raw: str | None) -> str | None:
    if not raw:
        return None
    token = raw.split()[0]  # first whitespace‑delimited token
    if not token:
        return None
    token = _ud.normalize("NFKC", token).lower()
    return token


def _parse_timestamp(ts: str | None) -> _dt.datetime | None:
    if ts is None:
        return None
    try:
        return _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        # Fallback: strict split
        try:
            return _dt.datetime.strptime(ts[:19], _ISO_FMT_COMPACT)
        except Exception:
            _LOG.debug("habit_consistency_reward: failed parsing timestamp %s", ts)
            return None


def _extract(result: Any) -> tuple[str | None, _dt.datetime | None]:
    if isinstance(result, dict):
        habit = _normalise_habit(result.get("context"))
        ts = _parse_timestamp(result.get("time"))
        return habit, ts
    return None, None


def _delta_hours(now: _dt.datetime, then: _dt.datetime) -> float:
    return abs((now - then).total_seconds()) / 3600.0


def _score_delta(hours: float) -> float:
    for thr, score in sorted(DELTA_THRESHOLDS.items()):
        if hours <= thr:
            return score
    return 0.0


# ───────────────────────────── main API ──────────────────────────────────────
def reward(state: Any, action: Any, result: Any) -> float:  # noqa: D401
    """Return a habit‑consistency reward in **[0.0, 1.0]**."""
    habit, ts = _extract(result)
    if habit is None or ts is None:
        return 0.0  # malformed – ignore

    with _lock:
        last = _last_seen.get(habit)
        _last_seen[habit] = ts

    if last is None:
        _LOG.debug("habit %s first seen at %s", habit, ts)
        return FIRST_SIGHT_REWARD

    delta = _delta_hours(ts, last)
    score = _score_delta(delta)
    _LOG.debug("habit %s delta %.1f h → score %.2f", habit, delta, score)
    return score
