# SPDX-License-Identifier: Apache-2.0
"""check_env network detection tests."""

import pytest
import subprocess
import check_env


def _no_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_env, "REQUIRED", [])
    monkeypatch.setattr(check_env, "OPTIONAL", [])
    monkeypatch.setattr(check_env, "warn_missing_core", lambda: [])


def test_offline_no_wheelhouse(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Fail fast when offline without a wheelhouse."""
    _no_missing(monkeypatch)
    monkeypatch.setattr(check_env, "has_network", lambda: False)
    monkeypatch.delenv("WHEELHOUSE", raising=False)
    rc = check_env.main(["--auto-install"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "--wheelhouse <dir>" in out
    assert "No network connectivity" in out


def test_offline_with_wheelhouse(monkeypatch: pytest.MonkeyPatch) -> None:
    """Allow offline installs when --wheelhouse is provided."""
    _no_missing(monkeypatch)
    monkeypatch.setattr(check_env, "has_network", lambda: False)
    def _fake_run(*_a, **_k):
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    rc = check_env.main(["--auto-install", "--wheelhouse", "wheels"])
    assert rc == 0
