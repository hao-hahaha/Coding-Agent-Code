# SPDX-License-Identifier: Apache-2.0
"""Regression tests for wheelhouse handling in check_env."""

import subprocess

import check_env


def _no_missing(monkeypatch):
    monkeypatch.setattr(check_env, "REQUIRED", [])
    monkeypatch.setattr(check_env, "OPTIONAL", [])
    monkeypatch.setattr(check_env, "warn_missing_core", lambda: [])


def test_empty_wheelhouse_fallback(tmp_path, monkeypatch, capsys):
    """Ensure empty wheelhouse is ignored and network install is used."""
    _no_missing(monkeypatch)
    empty = tmp_path / "wheels"
    empty.mkdir()
    monkeypatch.setattr(check_env, "has_network", lambda: True)

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, "", ""))
    rc = check_env.main(["--auto-install", "--wheelhouse", str(empty)])
    out = capsys.readouterr().out.lower()
    assert rc == 0
    assert "falling back to network" in out
