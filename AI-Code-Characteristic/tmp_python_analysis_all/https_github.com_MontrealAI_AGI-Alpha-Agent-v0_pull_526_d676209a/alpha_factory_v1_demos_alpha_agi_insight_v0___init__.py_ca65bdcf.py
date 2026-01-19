"""α‑AGI Insight demo package."""

# ``main`` gives callers the convenient entrypoint from ``__main__``.
from .__main__ import main  # re-export
from . import openai_agents_bridge
from .run_demo import main as run_demo
from .official_demo import main as official_demo

__all__ = ["main", "openai_agents_bridge", "run_demo", "official_demo"]
