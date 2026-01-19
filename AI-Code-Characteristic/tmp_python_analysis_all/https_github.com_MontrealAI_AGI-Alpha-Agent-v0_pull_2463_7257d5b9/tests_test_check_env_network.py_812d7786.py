# SPDX-License-Identifier: Apache-2.0
"""check_env network detection tests."""

import pytest
import subprocess
import urllib.request
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


def test_has_network_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return True when later test hosts are reachable."""

    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)

    attempts = []

    class _Sock:
        def __enter__(self) -> "_Sock":
            return self

        def __exit__(self, *exc: object) -> None:
            pass

    def _connect(addr: tuple[str, int], timeout: float = 1.0) -> _Sock:
        attempts.append(addr)
        if addr[0] == "pypi.org":
            raise OSError
        return _Sock()

    monkeypatch.setattr(check_env.socket, "create_connection", _connect)  # type: ignore[attr-defined]
    assert check_env.has_network() is True
    assert attempts == [("pypi.org", 443), ("1.1.1.1", 443)]


def test_has_network_all_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return False when none of the hosts are reachable."""

    monkeypatch.delenv("HTTP_PROXY", raising=False)
    monkeypatch.delenv("HTTPS_PROXY", raising=False)

    attempts = []

    def _connect(_addr: tuple[str, int], timeout: float = 1.0) -> None:
        attempts.append(_addr)
        raise OSError

    monkeypatch.setattr(check_env.socket, "create_connection", _connect)  # type: ignore[attr-defined]
    assert check_env.has_network() is False
    assert len(attempts) >= 3


def test_has_network_with_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure proxy variables are consulted for connectivity."""

    attempts: list[tuple[str, int]] = []

    class _Sock:
        def __enter__(self) -> "_Sock":
            return self

        def __exit__(self, *exc: object) -> None:
            pass

    def _connect(addr: tuple[str, int], timeout: float = 1.0) -> _Sock:
        attempts.append(addr)
        if addr[0] == "proxy.local":
            return _Sock()
        raise OSError

    monkeypatch.setenv("HTTP_PROXY", "http://proxy.local:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.local:8080")
    monkeypatch.setattr(check_env.socket, "create_connection", _connect)  # type: ignore[attr-defined]
    assert check_env.has_network() is True
    assert attempts[0] == ("proxy.local", 8080)


def test_has_network_head_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use urllib as fallback when socket connections fail."""

    def _connect(_addr: tuple[str, int], timeout: float = 1.0) -> None:
        raise OSError

    called: list[str] = []

    class _Resp:
        def __enter__(self) -> "_Resp":
            return self

        def __exit__(self, *exc: object) -> None:
            pass

    def _urlopen(req: object, timeout: float = 1.0) -> _Resp:
        called.append(getattr(req, "full_url", ""))
        return _Resp()

    monkeypatch.setenv("HTTP_PROXY", "http://proxy.local:3128")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.local:3128")
    monkeypatch.setattr(check_env.socket, "create_connection", _connect)  # type: ignore[attr-defined]
    monkeypatch.setattr(urllib.request, "urlopen", _urlopen)
    assert check_env.has_network() is True
    assert called and called[0].startswith("https://")
