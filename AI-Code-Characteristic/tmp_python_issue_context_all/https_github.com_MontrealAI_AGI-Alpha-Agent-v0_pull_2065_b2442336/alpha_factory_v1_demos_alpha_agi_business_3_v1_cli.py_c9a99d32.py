# SPDX-License-Identifier: Apache-2.0
"""Console entry point for the α‑AGI Business v3 demo."""
from __future__ import annotations

import asyncio

from .alpha_agi_business_3_v1 import main as _main


def main() -> None:
    """Run the asynchronous ``_main`` function via ``asyncio.run``."""
    asyncio.run(_main())
