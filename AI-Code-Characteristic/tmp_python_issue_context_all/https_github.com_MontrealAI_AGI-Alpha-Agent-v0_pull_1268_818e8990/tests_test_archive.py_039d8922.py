# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import json

import pytest

from src.archive.db import ArchiveDB, ArchiveEntry
from src.archive.service import ArchiveService
import src.archive.service as service
import asyncio
from unittest import mock


@pytest.fixture
def TestArchiveMigration(tmp_path):
    def _factory(entries):
        (tmp_path / "archive.json").write_text(json.dumps(entries))
        return ArchiveDB(tmp_path / "archive.db")

    return _factory


def test_archive_crud(tmp_path) -> None:
    db = ArchiveDB(tmp_path / "arch.db")
    root = ArchiveEntry("h1", None, 0.1, 0.0, True, 1.0)
    child = ArchiveEntry("h2", "h1", 0.2, 0.0, False, 2.0)
    db.add(root)
    db.add(child)

    assert db.get("h2") == child
    history = list(db.history("h2"))
    assert [e.hash for e in history] == ["h2", "h1"]


def test_archive_migration(TestArchiveMigration) -> None:
    entries = [
        {"hash": "a", "parent": None, "score": 0.3, "novelty": 0.1, "is_live": True, "ts": 1.0},
        {"hash": "b", "parent": "a", "score": 0.4, "novelty": 0.2, "is_live": False, "ts": 2.0},
    ]
    db = TestArchiveMigration(entries)
    assert db.get("a") is not None
    assert db.get("b").parent == "a"


def test_archive_service_chain_growth(tmp_path) -> None:
    svc = ArchiveService(tmp_path / "arch.db", broadcast=False)
    root1 = svc.insert_entry({"id": 1}, {"score": 0.1})
    first_hash = svc.last_hash()
    root2 = svc.insert_entry({"id": 2}, {"score": 0.2})
    second_hash = svc.last_hash()
    assert first_hash != second_hash
    assert svc.conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == 2
    parent = svc.conn.execute("SELECT parent FROM entries WHERE hash=?", (second_hash,)).fetchone()[0]
    assert parent == first_hash
    assert root1 != ""
    assert root2 != ""


def _dummy_classes(raise_err: bool = False):
    captured = {}

    class DummyClient:
        def __init__(self, url: str) -> None:
            captured["url"] = url

        async def send_transaction(self, tx: object, *args: object) -> None:
            if raise_err:
                raise RuntimeError("fail")
            captured["root"] = tx.instructions[0].data.decode()

        async def close(self) -> None:  # pragma: no cover - dummy
            pass

    class DummyTx:
        def __init__(self) -> None:
            self.instructions = []

        def add(self, instr: object) -> "DummyTx":
            self.instructions.append(instr)
            return self

    class DummyInstr:
        def __init__(self, program_id: object, data: bytes, keys: list[object]):
            self.data = data

    class DummyPk:
        def __init__(self, val: str) -> None:  # pragma: no cover - dummy
            pass

    return captured, DummyClient, DummyTx, DummyInstr, DummyPk


def test_archive_service_broadcast(tmp_path) -> None:
    svc = ArchiveService(tmp_path / "arch.db", rpc_url="http://rpc.test", broadcast=True)
    svc.insert_entry({"id": 1}, {"score": 0.1})
    root = svc.compute_merkle_root()
    captured, DummyClient, DummyTx, DummyInstr, DummyPk = _dummy_classes()
    with (
        mock.patch.object(service, "AsyncClient", DummyClient, create=True),
        mock.patch.object(service, "Transaction", DummyTx, create=True),
        mock.patch.object(service, "TransactionInstruction", DummyInstr, create=True),
        mock.patch.object(service, "PublicKey", DummyPk, create=True),
    ):
        asyncio.run(svc.broadcast_merkle_root())
    assert captured["url"] == "http://rpc.test"
    assert captured["root"] == root

