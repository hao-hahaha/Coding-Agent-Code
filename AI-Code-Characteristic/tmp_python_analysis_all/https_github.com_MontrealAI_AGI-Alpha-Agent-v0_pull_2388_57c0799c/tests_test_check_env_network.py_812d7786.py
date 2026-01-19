# SPDX-License-Identifier: Apache-2.0
"""check_env network detection tests."""

import pytest
import subprocess
import check_env

pytestmark = pytest.mark.smoke


def _no_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_env, "REQUIRED", [])
    monkeypatch.setattr(check_env, "OPTIONAL", [])
    monkeypatch.setattr(check_env, "warn_missing_core", lambda: [])


def test_offline_no_wheelhouse(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fallback to repo wheelhouse when offline and no option is given."""
    _no_missing(monkeypatch)
    monkeypatch.setattr(check_env, "has_network", lambda: False)
    monkeypatch.delenv("WHEELHOUSE", raising=False)
    rc = check_env.main(["--auto-install"])
    assert rc == 0


def test_offline_with_wheelhouse(monkeypatch: pytest.MonkeyPatch) -> None:
    """Allow offline installs when --wheelhouse is provided."""
    _no_missing(monkeypatch)
    monkeypatch.setattr(check_env, "has_network", lambda: False)

    from typing import Any

    def _fake_run(*_a: Any, **_k: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    rc = check_env.main(["--auto-install", "--wheelhouse", "wheels"])
    assert rc == 0


def test_skip_net_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure --skip-net-check avoids connectivity checks."""
    _no_missing(monkeypatch)

    def _fail_net() -> bool:
        raise AssertionError("has_network called")

    monkeypatch.setattr(check_env, "has_network", _fail_net)
    rc = check_env.main(["--auto-install", "--skip-net-check"])
    assert rc == 0
