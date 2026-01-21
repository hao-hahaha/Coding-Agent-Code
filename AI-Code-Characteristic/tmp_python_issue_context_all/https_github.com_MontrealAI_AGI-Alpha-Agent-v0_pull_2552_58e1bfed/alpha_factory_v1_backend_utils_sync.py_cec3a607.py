# SPDX-License-Identifier: Apache-2.0
"""Helper utilities for running async code synchronously."""

from __future__ import annotations

import asyncio
import threading
from typing import Awaitable, TypeVar

T = TypeVar("T")


def run_sync(coro: Awaitable[T]) -> T:
    """Run ``coro`` synchronously regardless of event loop state."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: list[T] = []

    def _worker() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(coro)
        try:
            result.append(loop.run_until_complete(task))
        finally:
            loop.close()

    t = threading.Thread(target=_worker)
    t.start()
    t.join()
    return result[0]
