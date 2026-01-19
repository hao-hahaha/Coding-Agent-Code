# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import asyncio

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import (
    chaos_agent,
    memory_agent,
    safety_agent,
)
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import (
    config,
    messaging,
    logging,
)
from google.protobuf import struct_pb2


def test_malicious_message_blocked(tmp_path) -> None:
    if not hasattr(struct_pb2.Struct, "get"):
        def _get(self: struct_pb2.Struct, key: str, default=None):
            try:
                return self[key]
            except Exception:
                return default

        struct_pb2.Struct.get = _get  # type: ignore[attr-defined]

    cfg = config.Settings(bus_port=0)
    bus = messaging.A2ABus(cfg)
    ledger = logging.Ledger(str(tmp_path / "ledger.db"), broadcast=False)

    mem = memory_agent.MemoryAgent(bus, ledger, str(tmp_path / "mem.log"))
    guardian = safety_agent.SafetyGuardianAgent(bus, ledger)
    chaos = chaos_agent.ChaosAgent(bus, ledger, burst=1)

    async def run() -> None:
        async with bus, ledger:
            await chaos.run_cycle()
            await asyncio.sleep(0)

    asyncio.run(run())

    assert mem.records
    assert mem.records[-1]["status"] == "blocked"
