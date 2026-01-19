from pathlib import Path

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging


def test_merkle_root_ignores_corrupt_rows(tmp_path: Path) -> None:
    ledger = Ledger(str(tmp_path / "ledger.db"), broadcast=False)
    env1 = messaging.Envelope(sender="a", recipient="b", payload={"v": 1}, ts=0.0)
    env2 = messaging.Envelope(sender="b", recipient="c", payload={"v": 2}, ts=1.0)
    ledger.log(env1)
    ledger.log(env2)

    baseline = ledger.compute_merkle_root()

    # insert rows with missing hash and invalid hash
    ledger.conn.execute(
        "INSERT INTO messages (ts, sender, recipient, payload) VALUES (?, ?, ?, ?)",
        (2.0, "x", "y", "{oops"),
    )
    ledger.conn.execute(
        "INSERT INTO messages (ts, sender, recipient, payload, hash) VALUES (?, ?, ?, ?, ?)",
        (3.0, "y", "z", "{}", "zz"),
    )
    ledger.conn.commit()

    root = ledger.compute_merkle_root()
    assert root == baseline

    # further logging should still succeed
    ledger.log(messaging.Envelope(sender="c", recipient="d", payload={"v": 3}, ts=2.0))
    ledger.compute_merkle_root()

