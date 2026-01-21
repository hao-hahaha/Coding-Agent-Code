
"""
education_reward.py  – Era‑of‑Experience demo
--------------------------------------------
Grounds the *learning / cognitive stimulation* pillar proposed by
Silver & Sutton (“The Era of Experience”, 2024).  The heuristic below
encourages the agent to:

* diversify the skills it practises         (+0.1 … +0.3)
* allocate enough *quality* time per study  (+0.0 … +0.4)
* progress toward mastery (spaced‑repetition bias) (+0.0 … +0.3)

The reward is deliberately *dense* (every event evaluated), fast to
compute (< 50 µs) and free of external API calls so it can run fully
offline.

API
===
```
reward(state, action, result) -> float  # required by back‑end loader
```
The *state* is assumed to expose:

    .history  – deque[dict]  (chronological interaction events)
    .clock    – datetime     (UTC)

while *action* / *result* match the conventions of the Alpha‑Factory
orchestrator (tool name, arguments, observation payload).

This lax typing means you can pass any dict‑like shim when testing.
"""

from __future__ import annotations

import math
import random
from collections import Counter, deque
from datetime import timedelta
from typing import Any, Dict

# ----------------------------- helpers --------------------------------------


def _skill_from_event(evt: Dict[str, Any]) -> str | None:
    """Extract a coarse skill tag from an experience event."""
    ctx = (evt.get("context") or "").lower()
    for kw in ("duolingo", "language", "spanish", "french", "japanese"):
        if kw in ctx:
            return "language"
    for kw in ("coding", "leetcode", "programming", "python"):
        if kw in ctx:
            return "coding"
    if "lecture" in ctx or "course" in ctx:
        return "course"
    return None


def _exponential_decay(dt_seconds: float, half_life: float = 60 * 60 * 6) -> float:
    """Half‑life decay weighting (default 6 h)."""
    return 2 ** (-dt_seconds / half_life)


# ----------------------------- reward core ----------------------------------


def reward(state: Any, action: Any, result: Any) -> float:
    """Return a float in the range [0, 1] encouraging deliberate practice.

    Rules (additive):
    ┌─────────────┬───────────────────────────────────────────┬─────────────┐
    │ Component    │ Heuristic                               │ Range       │
    ├─────────────┼───────────────────────────────────────────┼─────────────┤
    │ Diversity    │ New skill unseen in prev 24 h            │ +0.15       │
    │               │ 2nd new skill                           │ +0.05       │
    │ Session time │ >15 min of learning context              │ +0.10–0.40  │
    │ Mastery      │ Right‑spaced repetition of same skill    │ +0.05–0.25  │
    └─────────────┴───────────────────────────────────────────┴─────────────┘
    """

    # --- prerequisites ------------------------------------------------------
    history: deque = getattr(state, "history", deque(maxlen=0))
    now = getattr(state, "clock", None)

    # synthesise a timestamp if missing (e.g., during unit tests)
    if now is None:
        import datetime as _dt

        now = _dt.datetime.now(_dt.timezone.utc)

    # ------------------------------------------------------------------------
    # 1) Detect if the *result* represents a bona‑fide learning activity
    # ------------------------------------------------------------------------
    ctx = "".join(str(v).lower() for v in (result, action))
    if not any(
        kw in ctx
        for kw in (
            "duolingo",
            "completed lesson",
            "flashcards",
            "quiz",
            "watched lecture",
        )
    ):
        return 0.0  # not an education signal

    # ------------------------------------------------------------------------
    # 2) Skill tags & history analysis
    # ------------------------------------------------------------------------
    skill = _skill_from_event(result) or _skill_from_event(action) or "generic"

    last_24h = [
        evt
        for evt in history
        if (now - evt.get("time", now)).total_seconds() < 60 * 60 * 24
    ]
    skills_counter = Counter(_skill_from_event(evt) for evt in last_24h)

    diversity_bonus = 0.0
    if skills_counter[skill] == 0:
        diversity_bonus = 0.15
    elif skills_counter[skill] == 1:
        diversity_bonus = 0.05

    # ------------------------------------------------------------------------
    # 3) Session length approximation (if available)
    # ------------------------------------------------------------------------
    minutes = 0.0
    if "duration" in result and isinstance(result["duration"], (int, float)):
        minutes = float(result["duration"]) / 60.0
    elif "context" in result and "min" in str(result["context"]):
        # crude regex‑free scrape e.g. "studied 25 min on ..."
        import re

        m = re.search(r"(\d{1,3})\s*min", result["context"].lower())
        if m:
            minutes = float(m.group(1))
    session_bonus = max(0.0, min(0.4, (minutes - 15) * 0.02))

    # ------------------------------------------------------------------------
    # 4) Mastery spacing (encourage revisiting after ~1 day)
    # ------------------------------------------------------------------------
    last_same_skill = next(
        (
            evt
            for evt in reversed(history)
            if _skill_from_event(evt) == skill
        ),
        None,
    )
    mastery_bonus = 0.0
    if last_same_skill:
        hours_gap = (now - last_same_skill.get("time", now)).total_seconds() / 3600.0
        if 16 <= hours_gap <= 36:
            mastery_bonus = 0.25
        elif 8 <= hours_gap < 16 or 36 < hours_gap <= 72:
            mastery_bonus = 0.10

    # ------------------------------------------------------------------------
    # 5) Aggregate with exponential decay weight (recent events matter more)
    # ------------------------------------------------------------------------
    recency_weight = _exponential_decay(0.0)  # always 1.0 for *this* event
    reward_value = recency_weight * (
        diversity_bonus + session_bonus + mastery_bonus
    )

    # Clip safeguard
    return max(0.0, min(1.0, reward_value + random.uniform(-0.01, 0.01)))
