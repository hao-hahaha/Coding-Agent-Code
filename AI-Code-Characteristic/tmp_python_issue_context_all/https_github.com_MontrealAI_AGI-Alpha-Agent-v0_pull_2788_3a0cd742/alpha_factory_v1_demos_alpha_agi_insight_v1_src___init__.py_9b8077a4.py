# SPDX-License-Identifier: Apache-2.0
"""Entry point for the Insight demo package.

This package exposes lightweight agents, the orchestrator and helper
utilities used by the α‑AGI Insight example. Interface layers under
``interface`` provide a CLI, optional Streamlit dashboards and a REST API.
"""

# Re-export frequently used modules so test imports remain stable
from __future__ import annotations

from .agents import planning_agent
from alpha_factory_v1.core import orchestrator
from alpha_factory_v1.core.self_evolution import self_improver

__all__ = ["planning_agent", "orchestrator", "self_improver"]
