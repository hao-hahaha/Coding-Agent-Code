# SPDX-License-Identifier: Apache-2.0
"""Patch evaluation harness using Docker-in-Docker."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

from src.eval.preflight import run_preflight
from src.governance.stake_registry import StakeRegistry
from alpha_factory_v1.demos.self_healing_repo import patcher_core

IMAGE = os.getenv("SELF_EVOLUTION_IMAGE", "python:3.11-slim")


def _run_tests(repo: Path) -> int:
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{repo}:/work",
        "-w",
        "/work",
        IMAGE,
        "pytest",
        "-q",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode


def apply_patch(repo: str | Path, diff: str) -> Tuple[bool, Path]:
    """Apply ``diff`` to ``repo`` inside a sandbox and run tests."""
    src = Path(repo).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="self-evo-"))
    shutil.copytree(src, tmp, dirs_exist_ok=True)
    patcher_core.apply_patch(diff, repo_path=str(tmp))
    run_preflight(tmp)
    rc = _run_tests(tmp)
    return rc == 0, tmp


def vote_and_merge(repo: str | Path, diff: str, registry: StakeRegistry, agent_id: str = "orch") -> bool:
    """Apply patch and merge if tests pass and fitness improves."""
    repo_path = Path(repo).resolve()
    proposal = hashlib.sha1(diff.encode()).hexdigest()
    baseline = float((repo_path / "metric.txt").read_text().strip())
    ok, patched = apply_patch(repo_path, diff)
    if not ok:
        registry.vote(proposal, agent_id, False)
        shutil.rmtree(patched)
        return False
    new_score = float((patched / "metric.txt").read_text().strip())
    improved = new_score > baseline
    registry.vote(proposal, agent_id, improved)
    accepted = improved and registry.accepted(proposal)
    if accepted:
        for src_file in patched.rglob("*"):
            if src_file.is_file():
                rel = src_file.relative_to(patched)
                dest = repo_path / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest)
        registry.archive_accept(agent_id)
    shutil.rmtree(patched)
    return accepted
