"""Logging utilities for tamper-evident message tracking."""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, cast

try:  # optional dependency for colorized output
    import coloredlogs  # type: ignore
except Exception:  # pragma: no cover - optional
    coloredlogs = None  # type: ignore

from . import messaging

try:  # optional dependency
    from blake3 import blake3
except Exception:  # pragma: no cover - fallback
    from hashlib import sha256 as blake3

try:  # optional dependency
    from solana.rpc.async_api import AsyncClient
    from solana.transaction import Transaction
    from solana.publickey import PublicKey
    from solana.transaction import TransactionInstruction
except Exception:  # pragma: no cover - offline fallback
    AsyncClient = None

_log = logging.getLogger(__name__)


def setup(level: str = "INFO") -> None:
    """Initialise the root logger if not configured."""

    if not logging.getLogger().handlers:
        fmt = "%(asctime)s %(levelname)s %(name)s | %(message)s"
        if coloredlogs is not None:
            coloredlogs.install(level=level, fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")
        else:
            logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S")


def _merkle_root(hashes: Iterable[str]) -> str:
    nodes: List[bytes] = [bytes.fromhex(h) for h in hashes]
    if not nodes:
        return cast(str, blake3(b"\x00").hexdigest())

    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        next_lvl: List[bytes] = []
        for i in range(0, len(nodes), 2):
            next_lvl.append(blake3(nodes[i] + nodes[i + 1]).digest())
        nodes = next_lvl
    return nodes[0].hex()


class Ledger:
    """Append-only SQLite ledger with periodic Merkle root broadcast."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL,
                sender TEXT,
                recipient TEXT,
                payload TEXT,
                hash TEXT
            )
            """
        )
        self.conn.commit()
        self._task: asyncio.Task[None] | None = None

    def log(self, env: messaging.Envelope) -> None:
        """Hash ``env`` and append to the ledger."""

        data = json.dumps(asdict(env), sort_keys=True).encode()
        digest = blake3(data).hexdigest()
        with self.conn:
            self.conn.execute(
                "INSERT INTO messages (ts, sender, recipient, payload, hash) VALUES (?, ?, ?, ?, ?)",
                (env.ts, env.sender, env.recipient, json.dumps(env.payload), digest),
            )

    def compute_merkle_root(self) -> str:
        cur = self.conn.execute("SELECT hash FROM messages ORDER BY id")
        hashes = [row[0] for row in cur.fetchall()]
        return _merkle_root(hashes)

    def tail(self, count: int = 10) -> List[dict[str, object]]:
        """Return the last ``count`` ledger entries."""

        cur = self.conn.execute(
            "SELECT ts, sender, recipient, payload FROM messages ORDER BY id DESC LIMIT ?",
            (count,),
        )
        rows = cur.fetchall()
        result: List[dict[str, object]] = []
        for ts, sender, recipient, payload in reversed(rows):
            try:
                data = json.loads(payload)
            except Exception:
                data = payload
            result.append({"ts": ts, "sender": sender, "recipient": recipient, "payload": data})
        return result

    async def broadcast_merkle_root(self) -> None:
        root = self.compute_merkle_root()
        if AsyncClient is None:
            _log.info("Merkle root %s", root)
            return
        try:
            client = AsyncClient("https://api.testnet.solana.com")
            memo_prog = PublicKey("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
            tx = Transaction().add(TransactionInstruction(program_id=memo_prog, data=root.encode(), keys=[]))
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

    def start_merkle_task(self, interval: int = 3600) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop(interval))

    async def stop_merkle_task(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:  # pragma: no cover - expected
                pass
            self._task = None

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None  # type: ignore[assignment]
