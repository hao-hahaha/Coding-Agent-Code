# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import random

from src.archive import Archive


def test_archive_insert_and_load(tmp_path) -> None:
    db = tmp_path / "a.db"
    arch = Archive(db)
    arch.add({"name": "a"}, 0.1)
    arch.add({"name": "b"}, 0.2)
    rows = arch.all()
    assert len(rows) == 2
    assert rows[0].meta["name"] == "a"


def test_sample_bias(tmp_path) -> None:
    db = tmp_path / "a.db"
    arch = Archive(db)
    arch.add({"name": "low"}, 0.0)
    arch.add({"name": "high"}, 1.0)
    random.seed(0)
    counts = {"low": 0, "high": 0}
    for _ in range(50):
        chosen = arch.sample(1)[0]
        counts[chosen.meta["name"]] += 1
    assert counts["high"] > counts["low"]
