
"""
curiosity_reward.py – Alpha‑Factory v1 👁️✨
------------------------------------------------
Reward backend that encourages agents to seek *novel* observations.

Formula
~~~~~~~
    reward = 1 / (1 + N_obs)

where **N_obs** is how many times the exact observation hash has been seen
*so far in this Python process*.  First‑time events => **1.0**, second
occurrence => **0.5**, third => **0.33**, ...

Implementation details
----------------------
• Stateless API expected by *reward_backends* :
      reward(state, action, result) -> float

• Observation uniqueness:
    - We SHA‑1 hash ``repr(result)`` truncated to 4 KB to bound memory.
    - Hash digest stored in an LRU map (maxlen = 50 000) to avoid
      unbounded growth during very long runs.

• Thread‑safety: a single ``threading.Lock`` protects the counter map.

• Zero third‑party dependencies – standard library only.

© 2025 Montreal.AI   Apache-2.0 License
"""

from __future__ import annotations

import hashlib
import logging
import threading
from collections import OrderedDict
from typing import Any, Dict

__all__ = ["reward"]

_LOG = logging.getLogger(__name__)

# ─────────────────────────── configuration ──────────────────────────────
_MAX_ENTRIES = 50_000           # LRU capacity for seen hashes
_HASH_TRUNCATE = 4096           # bytes of repr() to hash

# ─────────────────────────── internal state ─────────────────────────────
class _LRUCounter(OrderedDict):
    """Thread‑safe LRU counter mapping hash → count."""

    def __init__(self, max_len: int) -> None:
        super().__init__()
        self._max_len = max_len
        self._lock = threading.Lock()

    def increment(self, h: str) -> int:
        """Increment count for *h* and return the *previous* count."""
        with self._lock:
            prev = self.get(h, 0)
            self[h] = prev + 1
            self.move_to_end(h)

            if len(self) > self._max_len:
                # Pop the least‑recently used item
                popped_h, _ = self.popitem(last=False)
                _LOG.debug("[curiosity_reward] LRU evict %s", popped_h)
            return prev

_seen = _LRUCounter(_MAX_ENTRIES)

# ─────────────────────────── helpers ────────────────────────────────────
def _hash_observation(obs: Any) -> str:
    """Return a stable SHA‑1 hex digest for an arbitrary Python object."""
    data = repr(obs).encode("utf-8", errors="replace")[: _HASH_TRUNCATE]
    return hashlib.sha1(data).hexdigest()

# ─────────────────────────── public API ─────────────────────────────────
def reward(state: Any, action: Any, result: Any) -> float:  # noqa: D401
    """Compute curiosity reward ∈ (0, 1]."""
    h = _hash_observation(result)
    prev_count = _seen.increment(h)

    # Inverse frequency
    r = 1.0 / (1.0 + prev_count)
    _LOG.debug("[curiosity_reward] hash=%s prev=%d reward=%.4f", h, prev_count, r)
    return r
