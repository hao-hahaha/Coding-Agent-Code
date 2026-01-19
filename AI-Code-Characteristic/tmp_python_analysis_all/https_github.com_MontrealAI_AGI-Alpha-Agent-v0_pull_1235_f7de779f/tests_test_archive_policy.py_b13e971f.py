from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.archive.manager import PatchManager, _tool_roundtrip
import src.archive.manager as manager


def test_tool_roundtrip(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(manager, "REPO_ROOT", tmp_path)
    monkeypatch.setattr("src.self_edit.tools.REPO_ROOT", tmp_path)
    assert _tool_roundtrip()


def test_admit_policy(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(manager, "REPO_ROOT", tmp_path)
    monkeypatch.setattr("src.self_edit.tools.REPO_ROOT", tmp_path)
    db_path = tmp_path / "arch.db"
    mgr = PatchManager(db_path)
    diff = "--- a/foo\n+++ b/foo\n@@\n-a\n+b\n"
    parent = "root"

    monkeypatch.setattr(manager, "run_preflight", lambda _repo: None)
    monkeypatch.setattr(manager, "_tool_roundtrip", lambda: True)
    assert mgr.admit(diff, parent)
    h = hashlib.sha1(diff.encode()).hexdigest()
    stored = mgr.db.get_state(f"patch:{h}")
    assert json.loads(stored) == {"diff": diff, "parent": parent}

    diff2 = "--- a/foo\n+++ b/foo\n@@\n-a\n+c\n"
    monkeypatch.setattr(manager, "run_preflight", lambda _repo: (_ for _ in ()).throw(RuntimeError()))
    assert not mgr.admit(diff2, parent)
    h2 = hashlib.sha1(diff2.encode()).hexdigest()
    assert mgr.db.get_state(f"patch:{h2}") is None

    diff3 = "--- a/foo\n+++ b/foo\n@@\n-a\n+d\n"
    monkeypatch.setattr(manager, "run_preflight", lambda _repo: None)
    monkeypatch.setattr(manager, "_tool_roundtrip", lambda: False)
    assert not mgr.admit(diff3, parent)
    h3 = hashlib.sha1(diff3.encode()).hexdigest()
    assert mgr.db.get_state(f"patch:{h3}") is None
