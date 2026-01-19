"""fitness_reward · Alpha-Factory v1 👁
----------------------------------------------------------------------
Grounded reward back-end focused on *physical well-being*.

Signature expected by the `reward_backends` framework:
    reward(state: Any, action: Any, result: Any) -> float

`state`, `action`, and `result` can be *anything* the orchestrator chooses to
pass.  This implementation expects **mapping-like** objects whose `.get()`
method retrieves numeric sensor readings (floats / ints).  Missing readings
are softly ignored via sensible fall-backs.

Metrics & Targets
-----------------
| Key              | Target (ideal)   | Normalisation | Weight |
|------------------|------------------|---------------|--------|
| ``steps``        | 10_000 steps/day | linear        | 0.25   |
| ``resting_hr``   | 60 bpm           | inverse       | 0.30   |
| ``sleep_hours``  | 8 h/night        | bell curve    | 0.30   |
| ``cal_intake``   | 2_100 kcal/day   | bell curve    | 0.15   |

Normalised sub-scores lie in ``[0, 1]``. The blended reward *also* lies
in ``[0, 1]``; higher is better.

Design Notes
------------
* **Parameter-free** – targets & weights are constants for now; tune offline.
* **Stateless** – no parameter updates, safe for concurrent use.
* **Fast** – pure-Python, <20 µs runtime.
"""

from __future__ import annotations

import math
from typing import Mapping

__all__ = ["reward"]  # explicit export for auto-discovery tools

# ----------------------------------------------------------------------
# Constants (targets & weights)
# ----------------------------------------------------------------------
_TARGET_STEPS = 10_000      # per day
_TARGET_REST_HR = 60        # beats per minute
_TARGET_SLEEP = 8.0         # hours
_TARGET_CAL = 2_100         # kilocalories

_WEIGHTS = {
    "steps": 0.25,
    "resting_hr": 0.30,
    "sleep_hours": 0.30,
    "cal_intake": 0.15,
}
_EPS = 1e-9  # avoid divide-by-zero


# ----------------------------------------------------------------------
# Helper normalisation functions
# ----------------------------------------------------------------------
def _linear(value: float, target: float, cap: float | None = None) -> float:
    """Linearly scales ``value`` → [0, 1] with 1 at ``target``."""
    if cap is None:
        cap = 2 * target  # allow 2× target to reach 0
    v = max(min(value, cap), 0)
    return max(0.0, 1.0 - abs(v - target) / (cap - target + _EPS))


def _inverse(value: float, ideal: float) -> float:
    """Higher score the *closer* ``value`` is to *below* ``ideal``."""
    if value <= ideal:
        return 1.0
    # penalise by percentage over ideal
    return ideal / (value + _EPS)


def _bell(value: float, ideal: float, sigma: float = 0.15) -> float:
    """Gaussian-shaped around ``ideal`` (15% std default)."""
    return math.exp(-0.5 * ((value - ideal) / (sigma * ideal)) ** 2)


# ----------------------------------------------------------------------
# Public reward() entry point
# ----------------------------------------------------------------------
def reward(state: Mapping | None, action, result: Mapping | None) -> float:
    """Compute *fitness* reward."""
    src = result or {}

    # Extract with graceful fall-backs (None → target → neutral score)
    steps = float(src.get("steps", _TARGET_STEPS))
    hr = float(src.get("resting_hr", _TARGET_REST_HR))
    sleep = float(src.get("sleep_hours", _TARGET_SLEEP))
    cal = float(src.get("cal_intake", _TARGET_CAL))

    scores = {
        "steps": _linear(steps, _TARGET_STEPS, cap=2 * _TARGET_STEPS),
        "resting_hr": _inverse(hr, _TARGET_REST_HR),
        "sleep_hours": _bell(sleep, _TARGET_SLEEP),
        "cal_intake": _bell(cal, _TARGET_CAL),
    }

    # Weighted average
    total_w = sum(_WEIGHTS.values())
    blended = sum(scores[k] * _WEIGHTS[k] for k in scores) / (total_w + _EPS)
    # Clamp for numerical safety
    return float(max(0.0, min(1.0, blended)))
