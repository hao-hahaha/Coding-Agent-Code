# SPDX-License-Identifier: Apache-2.0
"""α‑AGI Insight demo package."""

# ``main`` gives callers the convenient entrypoint from ``__main__``.
from .__main__ import main  # re-export
from . import openai_agents_bridge
from .run_demo import main as run_demo
from .official_demo import main as official_demo
from .official_demo_final import main as official_demo_final
from .official_demo_production import main as official_demo_production
from .beyond_human_foresight import main as beyond_human_foresight
from .official_demo_zero_data import main as official_demo_zero_data
from .api_server import main as api_server
from .insight_dashboard import main as insight_dashboard

__all__ = [
    "main",
    "openai_agents_bridge",
    "run_demo",
    "official_demo",
    "official_demo_final",
    "official_demo_production",
    "official_demo_zero_data",
    "beyond_human_foresight",
    "api_server",
    "insight_dashboard",
]
