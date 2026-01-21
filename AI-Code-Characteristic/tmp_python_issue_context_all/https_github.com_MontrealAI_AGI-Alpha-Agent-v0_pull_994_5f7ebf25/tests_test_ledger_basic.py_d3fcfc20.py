from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging


def test_log_and_tail(tmp_path):
    ledger = Ledger(str(tmp_path / "ledger.db"), broadcast=False)
    e1 = messaging.Envelope("a", "b", {"v": 1}, 0.0)
    e2 = messaging.Envelope("b", "c", {"v": 2}, 1.0)
    ledger.log(e1)
    ledger.log(e2)
    tail = ledger.tail(2)
    assert tail[0]["payload"]["v"] == 1
    assert tail[1]["payload"]["v"] == 2
