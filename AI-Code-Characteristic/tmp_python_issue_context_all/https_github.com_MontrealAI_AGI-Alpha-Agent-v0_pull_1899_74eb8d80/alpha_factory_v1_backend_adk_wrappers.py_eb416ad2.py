# SPDX-License-Identifier: Apache-2.0
"""
backend/adk_wrappers.py
────────────────────────────────────────────────────────────────────────────
ADK façade classes that expose existing domain‑specific agents through the
Google Agent Development Kit runtime, adding:

• Structured task metadata (JSON Schema I/O, descriptions)
• Built‑in retry / timeout semantics
• Governance span + VC emission for every call
• Graceful fallback when ADK is unavailable (unit‑test / offline mode)
"""

from __future__ import annotations

from typing import Any, Dict

from backend.agents.manufacturing_agent import ManufacturingAgent
from backend.agents.biotech_agent import BiotechAgent
from backend.governance import decision_span

# ─── Optional ADK import (keeps ci green when adk not installed) ──────────
try:
    from adk import Agent, task, JsonSchema

    _ADK_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _ADK_AVAILABLE = False

    class Agent:  # pylint: disable=too-few-public-methods
        def __init__(self, name: str):
            self.name = name

    def task(**_kwargs):
        def _decorator(func):
            return func

        return _decorator

    JsonSchema = dict  # type: ignore


# ─────────────────────────────────────────────────────────────────────────
#  Manufacturing wrapper
# ─────────────────────────────────────────────────────────────────────────
class ManufacturingADK(Agent):
    """ADK‑compatible adapter around `ManufacturingAgent`."""

    def __init__(self) -> None:
        super().__init__(name="manufacturing")
        self.impl = ManufacturingAgent()

    @task(
        name="schedule_jobs",
        description="Return an optimal Gantt schedule for the given job list "
        "within the planning horizon (in hours).",
        input_schema=JsonSchema(
            {
                "type": "object",
                "properties": {
                    "jobs": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "Each job must include duration & constraints",
                    },
                    "horizon": {"type": "integer", "minimum": 1},
                },
                "required": ["jobs", "horizon"],
            }
        ),
        output_schema=JsonSchema(
            {
                "type": "object",
                "properties": {"gantt": {"type": "object"}, "makespan": {"type": "number"}},
                "required": ["gantt", "makespan"],
            }
        ),
        retries=2,
        timeout=30,
    )
    def schedule_jobs(self, *, jobs: list[dict[str, Any]], horizon: int) -> Dict[str, Any]:
        """Return an optimised schedule via :class:`ManufacturingAgent`."""
        with decision_span("manufacturing.schedule_jobs", jobs=len(jobs), horizon=horizon):
            return self.impl.schedule(jobs, horizon)


# ─────────────────────────────────────────────────────────────────────────
#  Biotech wrapper
# ─────────────────────────────────────────────────────────────────────────
class BiotechADK(Agent):
    """ADK‑compatible adapter around `BiotechAgent`."""

    def __init__(self) -> None:
        super().__init__(name="biotech")
        self.impl = BiotechAgent()

    @task(
        name="protein_optimise",
        description="Optimise a protein sequence for improved stability " "and expression.",
        input_schema=JsonSchema(
            {
                "type": "object",
                "properties": {"sequence": {"type": "string", "minLength": 10}},
                "required": ["sequence"],
            }
        ),
        output_schema=JsonSchema(
            {
                "type": "object",
                "properties": {"optimised_sequence": {"type": "string"}, "delta_stability": {"type": "number"}},
                "required": ["optimised_sequence", "delta_stability"],
            }
        ),
        retries=1,
        timeout=60,
    )
    def protein_optimise(self, *, sequence: str) -> Dict[str, Any]:
        """Optimise *sequence* via :class:`BiotechAgent`."""
        with decision_span("biotech.protein_optimise", length=len(sequence)):
            return self.impl.optimise(sequence)


# ─── Helper: registry for dynamic discovery (A2A, gRPC, etc.) ────────────
def adk_registry() -> Dict[str, Agent]:
    """
    Return a mapping of ADK agent‑name → instance, used by the A2A server
    shim and unit‑tests.  Falls back to direct `ManufacturingAgent` /
    `BiotechAgent` when ADK is not installed.
    """
    if _ADK_AVAILABLE:
        return {
            "manufacturing": ManufacturingADK(),
            "biotech": BiotechADK(),
        }
    # Fallback: expose original agents for local test mode
    return {
        "manufacturing": ManufacturingAgent(),
        "biotech": BiotechAgent(),
    }


__all__ = [
    "ManufacturingADK",
    "BiotechADK",
    "adk_registry",
]
