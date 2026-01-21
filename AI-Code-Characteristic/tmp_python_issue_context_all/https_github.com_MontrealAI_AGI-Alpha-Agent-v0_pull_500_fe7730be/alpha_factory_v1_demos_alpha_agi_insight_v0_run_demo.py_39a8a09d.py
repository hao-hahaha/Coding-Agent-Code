#!/usr/bin/env python3
"""Standalone launcher for the α‑AGI Insight demo.

This convenience wrapper allows running the demo directly via
``python run_demo.py``. It delegates to :mod:`alpha_factory_v1.demos.alpha_agi_insight_v0`
which automatically selects the best runtime (OpenAI Agents when available
with configured API keys, otherwise the offline CLI).
"""
from __future__ import annotations

import pathlib
import sys

if __package__ is None:  # pragma: no cover - allow execution via `python run_demo.py`
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
    __package__ = "alpha_factory_v1.demos.alpha_agi_insight_v0"

import importlib

main = importlib.import_module(
    "alpha_factory_v1.demos.alpha_agi_insight_v0.__main__"
).main

if __name__ == "__main__":  # pragma: no cover
    main()
