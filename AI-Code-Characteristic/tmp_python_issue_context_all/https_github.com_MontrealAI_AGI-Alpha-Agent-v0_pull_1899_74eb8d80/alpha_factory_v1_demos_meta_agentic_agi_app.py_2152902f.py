#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Meta-Agentic α-AGI orchestrator.

Launches the evolutionary demo and optionally the
Streamlit lineage dashboard in a single command.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
from pathlib import Path

from meta_agentic_agi_demo import meta_loop, DB


def main() -> None:
    ap = argparse.ArgumentParser(description="Run Meta-Agentic α-AGI demo")
    ap.add_argument("--gens", type=int, default=6, help="number of generations")
    ap.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "mistral:7b-instruct.gguf"),
        help="openai:gpt-4o | anthropic:claude-3-sonnet | mistral:7b-instruct.gguf",
    )
    ap.add_argument(
        "--ui",
        action="store_true",
        help="launch Streamlit lineage UI after the search loop",
    )
    ap.add_argument(
        "--db",
        type=Path,
        default=DB,
        help="path to lineage SQLite DB",
    )
    args = ap.parse_args()

    os.environ["METAAGI_DB"] = str(args.db)

    try:
        asyncio.run(meta_loop(args.gens, args.provider))
    except KeyboardInterrupt:
        return

    if args.ui:
        ui_path = Path(__file__).parent / "ui" / "lineage_app.py"
        print(f"\nStarting Streamlit UI → {ui_path}\n")
        subprocess.call(["streamlit", "run", str(ui_path)])


if __name__ == "__main__":
    main()
