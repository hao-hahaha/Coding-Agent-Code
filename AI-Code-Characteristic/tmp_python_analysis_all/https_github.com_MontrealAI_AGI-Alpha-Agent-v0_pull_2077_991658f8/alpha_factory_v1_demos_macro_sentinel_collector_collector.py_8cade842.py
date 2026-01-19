# SPDX-License-Identifier: Apache-2.0
"""Live-feed collector sidecar for Macro-Sentinel."""

from __future__ import annotations

import asyncio
import json
import logging

from alpha_factory_v1.demos.macro_sentinel.data_feeds import stream_macro_events

log = logging.getLogger("macro_collector")


async def main() -> None:
    """Poll live APIs and emit events via data_feeds."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    async for evt in stream_macro_events(live=True):
        log.info("event=%s", json.dumps(evt))


if __name__ == "__main__":  # pragma: no cover
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
