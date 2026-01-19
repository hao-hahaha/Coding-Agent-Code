# SPDX-License-Identifier: Apache-2.0
import sys
from pathlib import Path
import asyncio
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.agents import memory_agent
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging, logging


def test_memory_agent_file_persistence(tmp_path: Path) -> None:
    mem_file = tmp_path / "mem.log"
    cfg = config.Settings(bus_port=0, memory_path=str(mem_file))
    bus = messaging.A2ABus(cfg)
    ledger = logging.Ledger(str(tmp_path / "ledger.db"))
    agent = memory_agent.MemoryAgent(bus, ledger, str(mem_file))

    envs = [messaging.Envelope("a", "memory", {"idx": i}, 0.0) for i in range(3)]

    async def _run() -> None:
        async with bus, ledger:
            for env in envs:
                await agent.handle(env)

    asyncio.run(_run())

    entries = [json.loads(line) for line in mem_file.read_text(encoding="utf-8").splitlines()]
    assert [e["idx"] for e in entries] == list(range(3))

    agent2 = memory_agent.MemoryAgent(bus, ledger, str(mem_file))
    assert [r["idx"] for r in agent2.records] == list(range(3))
