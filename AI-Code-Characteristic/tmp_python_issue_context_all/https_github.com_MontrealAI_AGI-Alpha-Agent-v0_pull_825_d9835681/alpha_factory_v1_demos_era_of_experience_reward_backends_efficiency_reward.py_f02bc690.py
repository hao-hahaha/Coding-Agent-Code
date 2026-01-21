"""
efficiency_reward.py – Alpha‑Factory v1 👁️✨
───────────────────────────────────────────────────────────────────────────────
Reward backend that **encourages computational *and* economic efficiency**
while keeping the interface dead‑simple: just drop a lightweight dict in the
`result` field of a tool‑call and the orchestrator gets back a scalar reward in
the closed unit interval [0, 1].

──────────────────────────────── Example payload ─────────────────────────────

    result = {
        # latency of the *overall* action perceived by the user (ms)
        "latency_ms" : 820,
        # prompt + completion tokens for LLM calls (or total tokens for batch)
        "tokens"     : 125,
        # marginal direct cost (USD) – model call, API, e‑gress, etc.
        "cost_usd"   : 0.0014,
        # measured or estimated energy consumption (joules)
        "energy_j"   : 22.3,
        # task‑specific value/utility forecast in [0, 1] (optional, see below)
        "value"      : 0.67,
    }

If the producer cannot measure some fields *just omit them* – sensible
defaults, tuned for the AGI‑Alpha demo infra, kick in.

────────────────────────────── Scoring heuristic ──────────────────────────────

1. **Normalise** each “cost dimension” against an *aspirational baseline*
   (configurable via env‑vars; see BASELINES below).

2. **Aggregate** the normalised penalties with a weighted sum   *P*.

       P = 0.4·latency + 0.3·tokens + 0.2·cost + 0.1·energy

3. **Blend with task value** `v ∈ [0,1]` coming either from the caller or
   derived upstream by the orchestrator.

       reward = v / (1 + P)              →   0 … 1

   • Missing/zero `value` ⇒ neutral reward 0.0.
   • The function is monotonic ⬇️ in penalties, monotonic ⬆️ in value.
   • Asymptotes guarantee diminishing returns and bounded output.

──────────────────────────────── Design notes ─────────────────────────────────

▸ Zero external deps – pure Python ≥ 3.9.
▸ Offline friendly – no OSS libraries, no web calls.
▸ *Thread‑safe read‑only*; no shared mutable state.
▸ Baselines overrideable at runtime via env‑vars, allowing infra tuning.
▸ Explicit `__all__` aids IDEs / static analysers.
▸ Lint‑clean (ruff) & typed – good citizens inside larger codebases.

© 2025 Montreal.AI – Apache-2.0 License
"""

from __future__ import annotations

import logging
import os
from typing import Any

__all__ = ("reward",)

_log = logging.getLogger(__name__)

# ─────────────────────────── configurable baselines ───────────────────────────
def _env_float(name: str, default: float) -> float:
    """Fetch *name* from env or fall back to *default* (must be > 0)."""
    try:
        v = float(os.getenv(name, default))
        return v if v > 0 else default
    except Exception:  # noqa: BLE001
        return default


# Baseline targets (tweak for your infra or via env)
_LAT_MS: float   = _env_float("EFF_BSLN_LAT_MS",   500.0)   # ms
_TOKENS: float   = _env_float("EFF_BSLN_TOKENS",   1500.0)  # tokens
_COST_USD: float = _env_float("EFF_BSLN_COST_USD", 0.01)    # dollars
_ENERGY_J: float = _env_float("EFF_BSLN_ENERGY_J", 50.0)    # joules

# Weights for penalty blend – must sum to 1.0
_WEIGHTS = (0.4, 0.3, 0.2, 0.1)


# ───────────────────────────── helper functions ──────────────────────────────
def _norm(value: float, baseline: float) -> float:
    """Return non‑negative normalised cost component (value / baseline)."""
    if value <= 0 or baseline <= 0:
        return 0.0
    return value / baseline


def _clip01(x: float) -> float:
    """Clamp *x* to the closed [0,1] interval (handles NaNs gracefully)."""
    if not (x >= 0.0):  # catches NaN
        return 0.0
    if x > 1.0:
        return 1.0
    return x


# ──────────────────────────────── main entry ‑ API ───────────────────────────
def reward(state: Any, action: Any, result: Any) -> float:   # noqa: D401
    """
    Efficiency reward ∈ [0, 1]

    Parameters
    ----------
    state   : snapshot of agent/env *ignored* by this backend
    action  : last action taken *ignored*
    result  : mapping with cost metrics (see module docstring)

    Returns
    -------
    float – higher is better; 0.0 = neutral.
    """
    if not isinstance(result, dict):
        _log.debug("efficiency_reward: non‑dict result – neutral reward")
        return 0.0

    try:
        value = float(result.get("value", 0.0))
    except Exception:  # noqa: BLE001
        value = 0.0

    if value <= 0.0:
        return 0.0

    try:
        latency_p = _norm(float(result.get("latency_ms", 0.0)), _LAT_MS)
        tokens_p  = _norm(float(result.get("tokens", 0.0)),     _TOKENS)
        cost_p    = _norm(float(result.get("cost_usd", 0.0)),   _COST_USD)
        energy_p  = _norm(float(result.get("energy_j", 0.0)),   _ENERGY_J)

        penalty = (
            _WEIGHTS[0] * latency_p +
            _WEIGHTS[1] * tokens_p  +
            _WEIGHTS[2] * cost_p    +
            _WEIGHTS[3] * energy_p
        )

        reward_val = value / (1.0 + penalty)
    except Exception as exc:  # noqa: BLE001
        _log.warning("efficiency_reward: error during calc – %s", exc)
        return 0.0

    return _clip01(reward_val)
