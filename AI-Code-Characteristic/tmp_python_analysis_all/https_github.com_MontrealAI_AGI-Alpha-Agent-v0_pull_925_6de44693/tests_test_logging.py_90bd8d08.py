import asyncio
import json
import logging
from dataclasses import asdict
from pathlib import Path
from unittest import mock
import pytest

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import logging as insight_logging
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils.logging import Ledger
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import messaging


def test_compute_merkle_root(tmp_path: Path) -> None:
    ledger = Ledger(str(tmp_path / "l.db"), broadcast=False)
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


def test_broadcast_merkle_root_logs_root_when_disabled(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    ledger = Ledger(str(tmp_path / "l.db"), broadcast=False)
    env = messaging.Envelope("a", "b", {"v": 1}, 0.0)
    ledger.log(env)
    root = ledger.compute_merkle_root()

    caplog.set_level(logging.INFO)

    dummy = mock.Mock(side_effect=AssertionError("AsyncClient should not be used"))
    with mock.patch.object(insight_logging, "AsyncClient", dummy):
        asyncio.run(ledger.broadcast_merkle_root())

    assert not dummy.called
    assert any(f"Merkle root {root}" in r.getMessage() for r in caplog.records)
