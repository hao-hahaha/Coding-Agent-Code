#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Launch the α‑AGI Insight official demo.

This helper ensures the environment is verified before delegating to the
package entry point. It mirrors ``run_demo.py`` but automatically passes
``--verify-env`` so users always receive a dependency check.
"""
from __future__ import annotations

import importlib
import pathlib
import sys
from typing import List

if __package__ is None:  # pragma: no cover - allow direct execution
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))
    __package__ = "alpha_factory_v1.demos.alpha_agi_insight_v0"

from . import __main__, insight_demo


def main(argv: List[str] | None = None) -> None:
    """Run the α‑AGI Insight demo with environment validation."""
    insight_demo.verify_environment()
    __main__.main(argv)


if __name__ == "__main__":  # pragma: no cover
    main()
