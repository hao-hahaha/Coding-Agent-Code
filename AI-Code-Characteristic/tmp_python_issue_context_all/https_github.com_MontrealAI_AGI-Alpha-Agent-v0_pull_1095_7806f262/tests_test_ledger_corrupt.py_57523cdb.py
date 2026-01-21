import sqlite3
from pathlib import Path

import pytest

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging


def test_compute_merkle_root_corrupt(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger.db"
    ledger = Ledger(str(ledger_path), broadcast=False)
    ledger.log(messaging.Envelope(sender="a", recipient="b", payload={"v": 1}, ts=0.0))
    ledger.log(messaging.Envelope(sender="b", recipient="c", payload={"v": 2}, ts=1.0))

    # Corrupt the SQLite file by truncating it
    data = ledger_path.read_bytes()
    ledger_path.write_bytes(data[: len(data) // 2])

    with pytest.raises(sqlite3.DatabaseError):
        ledger.compute_merkle_root()
