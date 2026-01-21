# SPDX-License-Identifier: Apache-2.0
"""Analyse archive backtracks and generate a histogram."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import plotly.express as px

from src.archive.db import ArchiveDB, ArchiveEntry

DEFAULT_DB = Path(os.getenv("ARCHIVE_PATH", "archive.db"))
DEFAULT_OUT = Path(
    "alpha_factory_v1/demos/alpha_agi_insight_v1/docs/backtrack_hist.svg"
)


def _load_entries(db_path: Path) -> List[ArchiveEntry]:
    """Return all archive entries."""
    with sqlite3.connect(db_path) as cx:
        rows = list(
            cx.execute(
                "SELECT hash, parent, score, novelty, is_live, ts FROM archive"
            )
        )
    return [
        ArchiveEntry(
            hash=r[0],
            parent=r[1],
            score=float(r[2]),
            novelty=float(r[3]),
            is_live=bool(r[4]),
            ts=float(r[5]),
        )
        for r in rows
    ]


def count_backtracks(db_path: str | Path = DEFAULT_DB) -> List[int]:
    """Return backtrack counts for each chain in ``db_path``."""
    db_path = Path(db_path)
    entries = _load_entries(db_path)
    entry_map = {e.hash: e for e in entries}
    parents = {e.parent for e in entries if e.parent}
    leaves = [e.hash for e in entries if e.hash not in parents]
    counts: List[int] = []
    for leaf in leaves:
        history = [entry_map[h.hash] for h in ArchiveDB(db_path).history(leaf)]
        count = sum(
            1
            for child, parent in zip(history, history[1:])
            if child.score < parent.score
        )
        counts.append(count)
    return counts


def plot_histogram(counts: Iterable[int], out_file: str | Path = DEFAULT_OUT) -> None:
    """Save histogram of ``counts`` to ``out_file``."""
    df = pd.DataFrame({"backtracks": list(counts)})
    fig = px.histogram(df, x="backtracks")
    path = Path(out_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(path))


__all__ = ["count_backtracks", "plot_histogram"]
