# SPDX-License-Identifier: Apache-2.0
"""Replay top agents on alternate models and log the scores."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Iterable

from src.archive import Archive, Agent


DEFAULT_ARCHIVE = Path(os.getenv("ARCHIVE_PATH", "archive.db"))
DEFAULT_RESULTS = Path("results/transfer_matrix.csv")


def evaluate_agent(agent: Agent, model: str) -> float:
    """Return agent score when evaluated with ``model``.

    This placeholder implementation simply returns the archived score. Tests
    patch this function to provide deterministic mock values.
    """

    return agent.score


def run_transfer_test(
    models: Iterable[str],
    top_n: int,
    *,
    archive_path: str | Path = DEFAULT_ARCHIVE,
    out_file: str | Path = DEFAULT_RESULTS,
) -> None:
    """Evaluate the top ``top_n`` agents on each model and store a score matrix."""

    arch = Archive(archive_path)
    agents = sorted(arch.all(), key=lambda a: a.score, reverse=True)[:top_n]

    path = Path(out_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        model_list = list(models)
        writer.writerow(["id", *model_list])
        for agent in agents:
            row = [agent.id]
            for model in model_list:
                score = evaluate_agent(agent, model)
                row.append(f"{score:.3f}")
            writer.writerow(row)


__all__ = ["run_transfer_test", "evaluate_agent"]
