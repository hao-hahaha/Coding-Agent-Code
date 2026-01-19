#!/usr/bin/env python3
"""Launch the Beyond Human Foresight variant of the α‑AGI Insight demo.

This thin wrapper prints a short banner then delegates to
:mod:`official_demo_final`, inheriting automatic environment
verification, optional OpenAI Agents SDK integration and graceful
offline mode.  The behaviour mirrors ``alpha-agi-insight-final`` while
providing a flashier startup message.
"""
from __future__ import annotations

from typing import List

if __package__ is None:  # pragma: no cover - allow direct execution
    import pathlib
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
    __package__ = "alpha_factory_v1.demos.alpha_agi_insight_v0"

from .official_demo_final import main as _main
from .openai_agents_bridge import print_banner


def main(argv: List[str] | None = None) -> None:
    """Entry point for the Beyond Human Foresight demo."""
    print_banner()
    _main(argv)


if __name__ == "__main__":  # pragma: no cover
    main()
