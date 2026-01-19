# SPDX-License-Identifier: Apache-2.0
"""Append-only archive storing agent specs and evaluator scores."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, List

from src.evaluators.novelty import NoveltyIndex

try:
    from blake3 import blake3
except Exception:  # pragma: no cover - fallback
    from hashlib import sha256 as blake3

try:  # optional dependency
    from solana.rpc.async_api import AsyncClient
    from solana.transaction import Transaction
    from solana.publickey import PublicKey
    from solana.transaction import TransactionInstruction
except Exception:  # pragma: no cover - offline fallback
    AsyncClient = None  # type: ignore

_log = logging.getLogger(__name__)

_DEFAULT_DB = Path(os.getenv("ARCHIVE_PATH", "archive.db"))


def _merkle_root(hashes: Iterable[str]) -> str:
    nodes: List[bytes] = [bytes.fromhex(h) for h in hashes]
    if not nodes:
        return blake3(b"\x00").hexdigest()

    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        next_lvl: List[bytes] = []
        for i in range(0, len(nodes), 2):
            next_lvl.append(blake3(nodes[i] + nodes[i + 1]).digest())
        nodes = next_lvl
    return nodes[0].hex()


class ArchiveService:
    """Simple append-only archive with Merkle root broadcasting."""

    def __init__(
        self,
        path: str | Path = _DEFAULT_DB,
        *,
        rpc_url: str | None = None,
        wallet: str | None = None,
        broadcast: bool = True,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent TEXT,
                spec TEXT,
                scores TEXT,
                hash TEXT,
                ts REAL
            )
            """
        )
        self.conn.commit()
        self.rpc_url = rpc_url
        self.wallet = wallet
        self.broadcast = broadcast
        self._task: asyncio.Task[None] | None = None
        self.novelty = NoveltyIndex()
        try:
            cur = self.conn.execute("SELECT spec FROM entries")
            for (spec_text,) in cur.fetchall():
                if isinstance(spec_text, str):
                    self.novelty.add(spec_text)
        except Exception:  # pragma: no cover - index load errors
            _log.debug("Failed to rebuild novelty index", exc_info=True)

    def last_hash(self) -> str | None:
        """Return the most recent entry hash or ``None`` if empty."""
        cur = self.conn.execute("SELECT hash FROM entries ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else None

    def compute_merkle_root(self) -> str:
        """Return the Merkle root over all stored entry hashes."""
        cur = self.conn.execute("SELECT hash FROM entries ORDER BY id")
        hashes = [row[0] for row in cur.fetchall() if isinstance(row[0], str)]
        valid: List[str] = []
        for h in hashes:
            try:
                bytes.fromhex(h)
            except Exception:
                continue
            valid.append(h)
        return _merkle_root(valid)

    def insert_entry(
        self,
        spec: Mapping[str, Any],
        scores: Mapping[str, float],
        *,
        parent: str | None = None,
    ) -> str:
        """Add an entry and return the updated Merkle root."""
        parent = parent or self.last_hash()
        record = {"parent": parent, "spec": spec, "scores": dict(scores)}
        digest = blake3(json.dumps(record, sort_keys=True).encode()).hexdigest()
        with self.conn:
            self.conn.execute(
                "INSERT INTO entries(parent, spec, scores, hash, ts) VALUES(?,?,?,?,?)",
                (parent, json.dumps(spec), json.dumps(record["scores"]), digest, time.time()),
            )
        try:
            self.novelty.add(json.dumps(spec))
        except Exception:  # pragma: no cover - embed errors
            _log.debug("Failed to add spec to novelty index", exc_info=True)
        return self.compute_merkle_root()

    async def broadcast_merkle_root(self) -> None:
        """Publish the current Merkle root via Solana or log it."""
        try:
            root = self.compute_merkle_root()
        except Exception as exc:  # pragma: no cover - corruption
            _log.warning("Failed to compute Merkle root: %s", exc)
            return
        if AsyncClient is None or not self.broadcast:
            _log.info("Merkle root %s", root)
            return
        try:
            client = AsyncClient(self.rpc_url or "https://api.testnet.solana.com")
            memo_prog = PublicKey("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
            tx = Transaction().add(TransactionInstruction(program_id=memo_prog, data=root.encode(), keys=[]))
            signer = None
            if self.wallet:
                try:  # pragma: no cover - optional dependency
                    from solana.keypair import Keypair

                    signer = Keypair.from_secret_key(bytes.fromhex(self.wallet))
                except Exception as exc:  # noqa: BLE001 - invalid key
                    _log.warning("Invalid wallet key: %s", exc)
            if signer:
                await client.send_transaction(tx, signer)
            else:
                await client.send_transaction(tx)
            _log.info("Broadcasted Merkle root %s", root)
        except Exception as exc:  # pragma: no cover - network errors
            _log.warning("Failed to broadcast Merkle root: %s", exc)
        finally:
            try:
                await client.close()
            except Exception:  # pragma: no cover - ignore close errors
                pass

    async def _loop(self, interval: int) -> None:
        while True:
            await asyncio.sleep(interval)
            await self.broadcast_merkle_root()

    def start_merkle_task(self, interval: int = 86_400) -> None:
        """Schedule periodic Merkle root broadcasts."""
        if self._task is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:  # pragma: no cover - no loop in sync context
                _log.warning("Merkle task requires a running event loop")
                return
            self._task = loop.create_task(self._loop(interval))

    async def stop_merkle_task(self) -> None:
        """Cancel the broadcast task if it is running."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:  # pragma: no cover - expected
                pass
            self._task = None

    def close(self) -> None:
        """Close the underlying database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None  # type: ignore[assignment]

    def __enter__(self) -> "ArchiveService":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    async def __aenter__(self) -> "ArchiveService":
        self.start_merkle_task()
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.stop_merkle_task()
        self.close()


__all__ = ["ArchiveService"]
