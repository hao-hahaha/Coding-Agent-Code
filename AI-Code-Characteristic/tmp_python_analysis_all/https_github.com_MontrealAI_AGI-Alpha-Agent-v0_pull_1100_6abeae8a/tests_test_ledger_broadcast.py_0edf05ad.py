import asyncio
import os
import tempfile
import sys
from types import ModuleType
from typing import Any
from unittest import mock

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import logging as insight_logging
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging


def test_broadcast_merkle_root_sends_transaction() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = Ledger(os.path.join(tmp, "l.db"), rpc_url="http://rpc.test", broadcast=True)
        env = messaging.Envelope(sender="a", recipient="b", payload={"v": 1}, ts=0.0)
        ledger.log(env)
        root = ledger.compute_merkle_root()

        calls: list[tuple[str, Any]] = []

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


def test_broadcast_merkle_root_logs_on_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        ledger = Ledger(os.path.join(tmp, "l.db"), rpc_url="http://rpc.test", broadcast=True)
        env = messaging.Envelope(sender="a", recipient="b", payload={"v": 1}, ts=0.0)
        ledger.log(env)
        root = ledger.compute_merkle_root()

        captured: dict[str, Any] = {}

        class DummyClient:
            def __init__(self, url: str) -> None:
                captured["url"] = url

            async def send_transaction(self, tx: Any, *args: Any) -> None:
                captured["root"] = tx.instructions[0].data.decode()
                raise RuntimeError("fail")

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
            mock.patch.object(insight_logging, "_log") as log,
        ):
            asyncio.run(ledger.broadcast_merkle_root())

        assert captured["root"] == root
        log.warning.assert_called()
