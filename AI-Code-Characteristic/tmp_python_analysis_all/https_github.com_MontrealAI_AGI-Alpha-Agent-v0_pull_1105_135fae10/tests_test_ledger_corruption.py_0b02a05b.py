from pathlib import Path
from unittest import mock
import asyncio

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import logging as insight_logging
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging


def test_compute_merkle_root_with_malformed_row(tmp_path: Path) -> None:
    ledger = Ledger(str(tmp_path / "ledger.db"), broadcast=False)
    e1 = messaging.Envelope(sender="a", recipient="b", payload={"v": 1}, ts=0.0)
    e2 = messaging.Envelope(sender="b", recipient="c", payload={"v": 2}, ts=1.0)
    ledger.log(e1)
    ledger.log(e2)
    baseline = ledger.compute_merkle_root()
    # insert invalid hash value
    ledger.conn.execute(
        "INSERT INTO messages (ts, sender, recipient, payload, hash) VALUES (?, ?, ?, ?, ?)",
        (2.0, "x", "y", "{}", "zz"),
    )
    ledger.conn.commit()
    assert ledger.compute_merkle_root() == baseline


def test_broadcast_merkle_root_handles_corrupt_db(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.db"
    ledger = Ledger(str(ledger_path), rpc_url="http://rpc.test", broadcast=True)
    ledger.log(messaging.Envelope(sender="a", recipient="b", payload={"v": 1}, ts=0.0))
    ledger.compute_merkle_root()
    # truncate database file to simulate missing pages
    data = ledger_path.read_bytes()
    ledger_path.write_bytes(data[: len(data) // 2])
    with mock.patch.object(insight_logging, "_log") as log:
        asyncio.run(ledger.broadcast_merkle_root())
        log.warning.assert_called()
