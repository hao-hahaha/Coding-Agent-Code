import asyncio
import json
import os
import tempfile
from dataclasses import asdict
from types import ModuleType
from typing import Any
from unittest import mock
import sys

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import logging as insight_logging
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging


def test_compute_merkle_root_matches_manual() -> None:
    tmp = tempfile.TemporaryDirectory()
    ledger = Ledger(os.path.join(tmp.name, "l.db"), broadcast=False)

    envs = [
        messaging.Envelope("a", "b", {"v": 1}, 0.0),
        messaging.Envelope("b", "c", {"v": 2}, 1.0),
        messaging.Envelope("c", "d", {"v": 3}, 2.0),
    ]
    for env in envs:
        ledger.log(env)

    computed = ledger.compute_merkle_root()

    hashes = []
    for env in envs:
        data = json.dumps(asdict(env), sort_keys=True).encode()
        hashes.append(insight_logging.blake3(data).hexdigest())  # type: ignore[attr-defined]

    manual = insight_logging._merkle_root(hashes)
    assert computed == manual
    tmp.cleanup()


def test_broadcast_merkle_root_uses_async_client() -> None:
    tmp = tempfile.TemporaryDirectory()
    ledger = Ledger(os.path.join(tmp.name, "l.db"), rpc_url="http://rpc.test", broadcast=True)
    env = messaging.Envelope("a", "b", {"v": 1}, 0.0)
    ledger.log(env)
    root = ledger.compute_merkle_root()

    calls: list[Any] = []

    class DummyClient:
        def __init__(self, url: str) -> None:
            calls.append(("url", url))

        async def send_transaction(self, tx: Any, *args: Any) -> None:
            calls.append(("sent", tx.instructions[0].data.decode()))

        async def close(self) -> None:
            pass

    class DummyTx:
        def __init__(self) -> None:
            self.instructions: list[Any] = []

        def add(self, instr: Any) -> "DummyTx":
            self.instructions.append(instr)
            return self

    class DummyInstr:
        def __init__(self, program_id: Any, data: bytes, keys: list[Any]):
            self.data = data

    class DummyPk:
        def __init__(self, val: str) -> None:
            pass

    # ensure mock module hierarchy exists for patching
    with (
        mock.patch.dict(
            sys.modules,
            {
                "solana": ModuleType("solana"),
                "solana.rpc": ModuleType("solana.rpc"),
                "solana.rpc.async_api": ModuleType("solana.rpc.async_api"),
            },
        ),
        mock.patch("solana.rpc.async_api.AsyncClient", DummyClient, create=True),
        mock.patch.object(insight_logging, "AsyncClient", DummyClient, create=True),
        mock.patch.object(insight_logging, "Transaction", DummyTx, create=True),
        mock.patch.object(insight_logging, "TransactionInstruction", DummyInstr, create=True),
        mock.patch.object(insight_logging, "PublicKey", DummyPk, create=True),
    ):
        asyncio.run(ledger.broadcast_merkle_root())

    assert ("url", "http://rpc.test") in calls
    assert ("sent", root) in calls
    tmp.cleanup()
