# SPDX-License-Identifier: Apache-2.0
"""LLM-driven mutator mixing AI output with random edits."""

from __future__ import annotations

import random
from pathlib import Path

from ...utils.logging import Ledger
from src.tools.diff_mutation import propose_diff as _fallback_diff
from .code_diff import _parse_spec, _sync_chat, _offline

__all__ = ["LLMMutator"]


class LLMMutator:
    """Generate diffs from recent logs using an LLM with random noise."""

    def __init__(self, ledger: Ledger, *, rng: random.Random | None = None) -> None:
        self.ledger = ledger
        self._rng = rng or random.Random()

    def _log_slice(self, count: int = 5) -> str:
        rows = self.ledger.tail(count)
        lines = []
        for r in rows:
            lines.append(f"{r.get('sender')}->{r.get('recipient')}: {r.get('payload')}")
        return "\n".join(lines)

    def _random_patch(self, file_path: str) -> str:
        goal = f"random-{self._rng.randint(0, 9999)}"
        return _fallback_diff(file_path, goal)

    def generate_diff(self, repo_path: str, spec: str, *, lines: int = 5) -> str:
        """Return a unified diff implementing ``spec`` inside ``repo_path``."""
        rel, goal = _parse_spec(spec)
        file_path = str(Path(repo_path) / rel)

        patch = ""
        if not _offline():
            prompt = (
                f"Repository: {repo_path}\n"
                f"Change: {spec}\n"
                f"Recent logs:\n{self._log_slice(lines)}\n"
                "Produce a unified diff."
            )
            try:
                patch = _sync_chat(prompt)
            except Exception:
                patch = ""

        if not patch:
            patch = _fallback_diff(file_path, goal)

        if self._rng.random() < 0.3:
            patch += self._random_patch(file_path)

        if not patch.endswith("\n"):
            patch += "\n"
        return patch
