# SPDX-License-Identifier: Apache-2.0
"""Minimal self-improvement workflow using GitPython.

This module clones a repository, applies a unified diff patch, evaluates a
numeric score and logs the score delta.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Tuple

try:
    import git
except ModuleNotFoundError:  # pragma: no cover - optional
    git = None


def _evaluate(repo_path: Path, metric_file: str) -> float:
    """Return the numeric metric stored in ``metric_file`` inside ``repo_path``."""
    return float((repo_path / metric_file).read_text().strip())


def _log_delta(delta: float, log_file: Path) -> None:
    """Append ``delta`` with timestamp to ``log_file`` (JSON list)."""
    log: list[dict[str, float]]
    if log_file.exists():
        log = json.loads(log_file.read_text())
    else:
        log = []
    log.append({"ts": time.time(), "delta": delta})
    log_file.write_text(json.dumps(log))


def improve_repo(repo_url: str, patch_file: str, metric_file: str, log_file: str) -> Tuple[float, Path]:
    """Clone ``repo_url``, apply ``patch_file`` and log score delta.

    Returns the score delta and path to the cloned repository.
    """
    if git is None:
        raise RuntimeError("GitPython is required")
    repo_dir = Path(tempfile.mkdtemp(prefix="selfimprover-"))
    repo = git.Repo.clone_from(repo_url, repo_dir)
    baseline = _evaluate(repo_dir, metric_file)
    repo.git.apply(patch_file)
    repo.index.add([metric_file])
    repo.index.commit("apply patch")
    new_score = _evaluate(repo_dir, metric_file)
    delta = new_score - baseline
    _log_delta(delta, Path(log_file))
    return delta, repo_dir
