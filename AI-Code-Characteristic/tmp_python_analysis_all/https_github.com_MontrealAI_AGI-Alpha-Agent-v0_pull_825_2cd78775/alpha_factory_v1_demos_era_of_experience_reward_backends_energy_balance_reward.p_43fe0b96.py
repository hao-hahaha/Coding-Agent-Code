"""energy_balance_reward.py — Alpha‑Factory v1 👁️✨
========================================================================
Reward backend that promotes **healthy daily energy balance**.

Rationale
---------
According to nutrition science, keeping the gap between calories consumed
(*energy‑in*) and calories burned (*energy‑out* + *basal metabolic rate*)
within ≈ ±300 kcal is a simple yet actionable target for most adults who
want to maintain weight and metabolic health.

The agent’s runtime environment passes day‑level logs in *result*:

    {
        "date"         : "YYYY‑MM‑DD" or ISO‑8601 timestamp,
        "calories_in"  : 2450,     # kcal eaten during the day
        "calories_out" : 600,      # kcal burned through exercise
        "bmr"          : 1650      # optional, defaults to 1650 kcal
    }

A cumulative per‑day ledger is maintained (thread‑safe) so the agent may
emit **multiple** food / exercise events and still receive one coherent
reward for the whole day.

Scoring
-------
Let ``net = calories_in − (bmr + calories_out)``

=====================  ========
 |net| (kcal)            reward
---------------------  --------
 0 – 300                  1.0
 301 – 600                0.5
 > 600                    0.0
=====================  ========

Implementation notes
--------------------
* No external dependencies — pure Python ≥ 3.9.
* Thread‑safe via a single `threading.Lock`.
* Uses `logging` for observability instead of `print`.
* Resilient to malformed input (returns 0.0 and logs a warning).

Public API (required by reward_backends framework)
--------------------------------------------------
    reward(state, action, result) -> float

© 2025 Montreal.AI – Apache-2.0 License
"""

from __future__ import annotations

import datetime as _dt
import logging as _log
import threading as _th
from typing import Any, Dict, Tuple

_logger = _log.getLogger(__name__)

# ----------------------------------------------------------------------
# Internal cumulative ledger {<ISO‑day>: (cal_in, cal_out, bmr)}
# ----------------------------------------------------------------------
_ledger: Dict[str, Tuple[int, int, int]] = {}
_lock = _th.Lock()

_DEFAULT_BMR = 1650  # kcal, population‑level average

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _iso_day(date_str: str | None) -> str:
    """Return YYYY‑MM‑DD for *date_str* (or *today* if missing/parsing fail)."""
    if not date_str:
        return _dt.date.today().isoformat()
    try:
        return _dt.date.fromisoformat(date_str[:10]).isoformat()
    except Exception:
        try:
            # lenient parse of full ISO‑8601 timestamp
            return _dt.datetime.fromisoformat(date_str.replace("Z", "")).date().isoformat()
        except Exception:
            _logger.warning("energy_balance_reward: unparseable date %s", date_str)
            return _dt.date.today().isoformat()

def _as_int(val: Any, fallback: int = 0) -> int:
    try:
        return int(val)
    except Exception:
        return fallback

def _score(net: int) -> float:
    abs_net = abs(net)
    if abs_net <= 300:
        return 1.0
    if abs_net <= 600:
        return 0.5
    return 0.0

def _update_day(res: Dict[str, Any]) -> Tuple[int, int, int]:
    """Atomically update ledger and return aggregate tuple (cin, cout, bmr)."""
    day = _iso_day(res.get("date"))
    with _lock:
        cin, cout, bmr = _ledger.get(day, (0, 0, _DEFAULT_BMR))
        cin += _as_int(res.get("calories_in"))
        cout += _as_int(res.get("calories_out"))
        if "bmr" in res:
            bmr = max(0, _as_int(res["bmr"], _DEFAULT_BMR))
        _ledger[day] = (cin, cout, bmr)
        return _ledger[day]

# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def reward(state: Any, action: Any, result: Any) -> float:  # noqa: D401
    """Compute energy‑balance reward for the day that *result* belongs to."""
    if not isinstance(result, dict):
        _logger.debug("energy_balance_reward: result not a dict → 0.0 reward")
        return 0.0

    cal_in, cal_out, bmr = _update_day(result)
    net = cal_in - (bmr + cal_out)
    score = _score(net)

    _logger.debug(
        "energy_balance_reward: day=%s cal_in=%d cal_out=%d bmr=%d net=%d reward=%.2f",
        _iso_day(result.get("date")), cal_in, cal_out, bmr, net, score
    )
    return score

# ----------------------------------------------------------------------
# Unit test (run with `python energy_balance_reward.py`)
# ----------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import json as _json

    samples = [
        {"date": "2025-04-22", "calories_in": 2400, "calories_out": 600, "bmr": 1650},
        {"date": "2025-04-22", "calories_in": 200},  # same day, extra snack
        {"date": "2025-04-22", "calories_out": 150},  # extra walk
        {"date": "2025-04-23", "calories_in": 3100, "calories_out": 200},
    ]

    for r in samples:
        print(_json.dumps(r), "->", reward({}, {}, r))
