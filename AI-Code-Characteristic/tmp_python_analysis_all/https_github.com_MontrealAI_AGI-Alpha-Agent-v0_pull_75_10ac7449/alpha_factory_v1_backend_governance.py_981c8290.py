"""
backend/governance.py
────────────────────────────────────────────────────────────────────────────
Unified *production‑grade* governance layer for α‑Factory.

Features preserved from the original module
────────────────────────────────────────────────────────
• Profanity / dangerous‑content filter (`Governance.moderate`)
• Numeric guard‑rail for trading plans (`Governance.vet_plans`)
• Legacy re‑export: `from backend.governance import Memory`

New capabilities (inspired by agentic‑trading best practices)
────────────────────────────────────────────────────────
• `decision_span()` context manager:
    ‑ Starts an OpenTelemetry span for every critical decision.
    ‑ Emits a W3C Verifiable Credential signed with Ed25519.
    ‑ Non‑blocking IPFS persistence.
• Graceful stubs → module works when OpenTelemetry or `vc` libs are absent
  (keeps CI green and supports offline laptops).

This file is **drop‑in compatible**; no calling code changes required.
"""

from __future__ import annotations

import importlib
import logging
import os
import re
from contextlib import contextmanager
from typing import Any, Dict, List

from better_profanity import profanity

# ── legacy re‑export (tests import Memory from this module) ────────────────
from .memory import Memory  # noqa: F401

# ╭────────────────────────────────────────────────────────────────────────╮
# │ 1.  Content‑policy guard‑rails (unchanged from original)               │
# ╰────────────────────────────────────────────────────────────────────────╯
_DANGER_PATTERNS: List[str] = [
    # Explosives
    r"\bbomb recipe\b",
    r"\bhow\s+to\s+(make|build).*?(bomb|explosive)\b",
    # Extremism
    r"\b(extremist|terrorist)\b",
    r"\b(extremist|terrorist).*?propaganda\b",
    r"\bpropaganda.*?(extremist|terrorist)\b",
    # Illicit finance / money‑laundering
    r"\blaunder\b",
    r"\bmoney laundering\b",
    # Violence
    r"\bkill\b",
]
_EXTRA = os.getenv("GOVERNANCE_EXTRA_PATTERNS", "")
if _EXTRA:
    _DANGER_PATTERNS.extend(p.strip() for p in _EXTRA.split(',') if p.strip())
_DANGER_RE = re.compile("|".join(_DANGER_PATTERNS), re.IGNORECASE)


class Governance:
    """
    Runtime guard‑rail service used by planners & agents.

    Methods
    -------
    moderate(text) -> bool
        True if `text` is safe to emit / display.
    vet_plans(agent, plans) -> list
        Returns a filtered list of plans respecting numeric limits.
    """

    def __init__(self, memory: Memory) -> None:
        self.log = logging.getLogger("Governance")
        self.memory = memory
        self.trade_limit = float(os.getenv("ALPHA_TRADE_LIMIT", "1000000"))
        profanity.load_censor_words()

    def update_trade_limit(self, new_limit: float) -> None:
        """Dynamically update :attr:`trade_limit` and log the change."""
        self.trade_limit = float(new_limit)
        self.log.info("Trade limit updated to %s", self.trade_limit)

    def describe(self) -> str:
        """Return a short human-readable summary of current policy."""
        return (
            f"Trade limit: {self.trade_limit}; "
            f"danger patterns: {len(_DANGER_PATTERNS)}"
        )

    # ── content guard‑rail --------------------------------------------------
    def moderate(self, text: str) -> bool:
        """Return **True** iff *text* passes policy checks."""
        if _DANGER_RE.search(text):
            self.log.warning("Blocked disallowed content: %s", text)
            return False
        if profanity.contains_profanity(text):
            self.log.warning("Blocked profanity: %s", text)
            return False
        return True

    # ── action / numeric guard‑rail ----------------------------------------
    def vet_plans(self, agent, plans: List[Dict[str, Any]]):
        """Strip plans that violate numeric policy (e.g., notional > limit)."""
        vetted = []
        for p in plans:
            if p.get("type") == "trade" and p.get("notional", 0) > self.trade_limit:
                self.log.warning("Blocked high‑notional trade: %s", p)
                self.memory.write(agent.name, "blocked", p)
                continue
            vetted.append(p)
        return vetted


# ╭────────────────────────────────────────────────────────────────────────╮
# │ 2.  Decision telemetry & credential emission                           │
# ╰────────────────────────────────────────────────────────────────────────╯
# Optional‑import OpenTelemetry (keeps repo usable without it)
_ot_trace_spec = importlib.util.find_spec("opentelemetry.trace")
if _ot_trace_spec:
    from opentelemetry import trace as _trace  # type: ignore
    _tracer = _trace.get_tracer("alpha_factory")
else:  # stub tracer
    class _DummySpan:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def get_span_context(self): return type("ctx", (), {"trace_id": 0})()
    class _DummyTracer:  # pylint: disable=too-few-public-methods
        def start_as_current_span(self, *_a, **_kw): return _DummySpan()
    _tracer = _DummyTracer()

# Optional‑import VC helper library
_vc_spec = importlib.util.find_spec("vc")
if _vc_spec:
    from vc import Credential, sign  # type: ignore
else:
    class _DummyCred(dict):  # type: ignore
        def __init__(self, **kw): super().__init__(kw)
    def _dummy_sign(c):  # pylint: disable=unused-argument
        class _Sig:
            def store_ipfs(self): return None
        return _Sig()
    Credential, sign = _DummyCred, _dummy_sign  # type: ignore

_VC_ENABLED = os.getenv("GOVERNANCE_DISABLE_CREDENTIALS", "false").lower() != "true"


@contextmanager
def decision_span(name: str, **attrs):
    """
    Context manager for critical decisions.

    Usage
    -----
    with decision_span("finance.open_trade", symbol="BTCUSD", qty=1):
        broker.place_order(...)
    """
    with _tracer.start_as_current_span(name, attributes=attrs) as span:
        yield span
        if _VC_ENABLED:
            cred = Credential(
                id=name,
                attrs=attrs | {"trace_id": getattr(span.get_span_context(), "trace_id", 0)},
            )
            try:
                sign(cred).store_ipfs()  # non‑blocking
            except Exception:  # pylint: disable=broad-except
                logging.getLogger("Governance").exception("VC signing failed")


__all__ = ["Governance", "Memory", "decision_span"]
