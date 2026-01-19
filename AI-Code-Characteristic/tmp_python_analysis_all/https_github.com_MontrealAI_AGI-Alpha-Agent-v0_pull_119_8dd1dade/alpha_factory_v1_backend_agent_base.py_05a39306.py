# SPDX-License-Identifier: Apache-2.0
"""Compatibility Agent base-class used across Alpha‑Factory.

This module preserves the historic ``backend.agent_base.AgentBase`` import
location while providing a thin, production‑ready implementation.  Each agent
cycle is traced, persisted and guarded by :mod:`backend.governance` so
behaviour can be replayed and audited.
"""

from __future__ import annotations

import abc
import asyncio
import datetime as _dt
import logging
import uuid
from typing import Any, Dict, List

from .tracer import Tracer


async def _maybe_async(fn, *args, **kwargs):
    """Run ``fn`` in the appropriate context (sync or async)."""
    if asyncio.iscoroutinefunction(fn):
        return await fn(*args, **kwargs)
    return await asyncio.to_thread(fn, *args, **kwargs)

class AgentBase(abc.ABC):
    """
    Shared skeleton for every domain agent:

        • observe() → collect data
        • think()   → propose tasks / ideas
        • act()     → execute vetted tasks

    Each phase is traced and persisted so evaluation harnesses can
    replay or diff behaviour across versions.
    """

    # ────────────────────────────────────────────────────────────────
    def __init__(self, name: str, model: Any, memory: Any, gov: Any) -> None:
        self.id = str(uuid.uuid4())
        self.name = name
        self.model = model
        self.memory = memory
        self.gov = gov

        self.log = logging.getLogger(name)
        self.tracer = Tracer(self.memory)

    # ───────── framework hooks (must be implemented) ───────────────
    def observe(self) -> List[Dict[str, Any]]:
        """Collect observations from the environment.

        Subclasses may override this method.  The default implementation
        returns an empty list so that legacy agents relying solely on a
        custom ``run_cycle`` can still be instantiated without implementing
        the observe/think/act trio explicitly.
        """
        return []

    def think(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process *observations* and return proposed tasks.

        Provided for backwards compatibility with early AgentBase versions.
        The base implementation simply returns an empty list.
        """
        return []

    def act(self, tasks: List[Dict[str, Any]]) -> None:
        """Execute approved *tasks*.

        The default body performs no action.  Concrete agents overriding
        :meth:`run_cycle` directly are therefore not forced to implement
        this method, preserving historical behaviour.
        """
        return None

    # ───────── single life‑cycle ───────────────────────────────────
    async def run_cycle(self) -> None:
        """Execute one Observe → Think → Act cycle with tracing."""
        ts = _dt.datetime.utcnow().isoformat()
        self.log.info("%s cycle start", self.name)

        try:
            observations = await _maybe_async(self.observe)
            self.tracer.record(self.name, "observe", observations)

            ideas = await _maybe_async(self.think, observations)
            self.tracer.record(self.name, "think", ideas)

            vetted = self.gov.vet_plans(self, ideas)
            self.tracer.record(self.name, "vet", vetted)

            await _maybe_async(self.act, vetted)
            self.tracer.record(self.name, "act", vetted)

        except Exception as err:  # pragma: no cover - safety net
            self.log.exception("Cycle error: %s", err)
            self.memory.write(
                self.name,
                "error",
                {"msg": str(err), "ts": ts},
            )

        self.log.info("%s cycle end", self.name)


__all__ = ["AgentBase"]

