"""Logging setup for the demo."""
from __future__ import annotations

import logging


def setup(level: str = "INFO") -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
