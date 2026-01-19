#!/usr/bin/env python3
"""Command line entrypoint for the α‑AGI Insight demo.

This tiny wrapper lets users run ``python -m alpha_factory_v1.demos.alpha_agi_insight_v0``
directly.  By default it delegates to :mod:`openai_agents_bridge` so the demo
can be controlled via the OpenAI Agents runtime when available.  Use
``--offline`` to force the simpler command line interface from
``insight_demo.py``.
"""
from __future__ import annotations

import argparse
from . import openai_agents_bridge, insight_demo
import os


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the α‑AGI Insight demo")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run the basic CLI without the OpenAI Agents runtime",
    )
    args, remainder = parser.parse_known_args(argv)

    # Soften noisy logs from the wider Alpha‑Factory environment.
    os.environ.setdefault("LOGLEVEL", "WARNING")

    if args.offline:
        insight_demo.main(remainder)
    else:
        openai_agents_bridge.main(remainder)


if __name__ == "__main__":  # pragma: no cover
    main()

