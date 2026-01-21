# SPDX-License-Identifier: Apache-2.0
"""Tests for the Macro-Sentinel run script."""

from __future__ import annotations

import os
import shutil
import subprocess
import re
from pathlib import Path

import pytest

RUN_SCRIPT = Path("alpha_factory_v1/demos/macro_sentinel/run_macro_demo.sh")


def _run_script(tmp_path: Path, *, env: dict[str, str], curl_rc: int = 0) -> tuple[str, str]:
    docker_log = tmp_path / "docker.log"
    curl_log = tmp_path / "curl.log"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    docker_stub = bin_dir / "docker"
    docker_stub.write_text(
        "#!/usr/bin/env bash\n"
        'echo "OLLAMA_BASE_URL=$OLLAMA_BASE_URL" >> "$DOCKER_LOG"\n'
        'echo "$@" >> "$DOCKER_LOG"\n'
        'if [ "$1" = "info" ]; then echo "{}"; fi\n'
        'if [ "$1" = "version" ]; then echo "24.0.0"; fi\n'
        "exit 0\n"
    )
    docker_stub.chmod(0o755)

    curl_stub = bin_dir / "curl"
    curl_stub.write_text("#!/usr/bin/env bash\n" 'echo "$@" >> "$CURL_LOG"\n' f"exit {curl_rc}\n")
    curl_stub.chmod(0o755)

    script_env = os.environ.copy()
    script_env.update(env)
    script_env.update(
        {
            "PATH": f"{bin_dir}:{script_env['PATH']}",
            "DOCKER_LOG": str(docker_log),
            "CURL_LOG": str(curl_log),
        }
    )

    config = RUN_SCRIPT.parent / "config.env"
    try:
        result = subprocess.run(
            [f"./{RUN_SCRIPT.name}"],
            cwd=RUN_SCRIPT.parent,
            env=script_env,
            capture_output=True,
            text=True,
        )
    finally:
        if config.exists():
            config.unlink()

    assert result.returncode == 0, result.stderr
    return docker_log.read_text(), curl_log.read_text()


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")  # type: ignore[misc]
def test_run_macro_demo_no_offline(tmp_path: Path) -> None:
    """`OPENAI_API_KEY` disables the offline profile."""
    docker_log, _ = _run_script(tmp_path, env={"OPENAI_API_KEY": "dummy-key"})
    assert "--profile offline" not in docker_log


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")  # type: ignore[misc]
def test_run_macro_demo_health_check(tmp_path: Path) -> None:
    """Health gate should hit the expected endpoint."""
    _, curl_log = _run_script(tmp_path, env={"OPENAI_API_KEY": "dummy-key"})
    assert "http://localhost:7864/healthz" in curl_log


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")  # type: ignore[misc]
def test_run_macro_demo_offline_download(tmp_path: Path) -> None:
    """Missing offline CSVs should trigger downloads."""
    offline_dir = RUN_SCRIPT.parent / "offline_samples"
    backup = tmp_path / "offline_backup"
    offline_dir.rename(backup)
    offline_dir.mkdir()
    try:
        _, curl_log = _run_script(tmp_path, env={"OPENAI_API_KEY": "dummy-key"})
    finally:
        shutil.rmtree(offline_dir)
        backup.rename(offline_dir)

    assert "fed_speeches.csv" in curl_log
    assert "yield_curve.csv" in curl_log
    assert "stable_flows.csv" in curl_log
    assert "cme_settles.csv" in curl_log


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")  # type: ignore[misc]
def test_run_macro_demo_download_failure_fallback(tmp_path: Path) -> None:
    """Failed downloads should copy placeholder CSVs."""
    offline_dir = tmp_path / "data"
    env = {
        "OPENAI_API_KEY": "dummy-key",
        "OFFLINE_DATA_DIR": offline_dir.as_posix(),
    }
    _run_script(tmp_path, env=env, curl_rc=1)
    for f in [
        "fed_speeches.csv",
        "yield_curve.csv",
        "stable_flows.csv",
        "cme_settles.csv",
    ]:
        path = offline_dir / f
        assert path.exists(), f"missing {f}"
        assert path.stat().st_size > 0


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")  # type: ignore[misc]
def test_run_macro_demo_passes_base_url(tmp_path: Path) -> None:
    """Custom OLLAMA_BASE_URL should reach docker compose."""
    env = {"OLLAMA_BASE_URL": "http://example.com/v1"}
    docker_log, _ = _run_script(tmp_path, env=env)
    assert "OLLAMA_BASE_URL=http://example.com/v1" in docker_log


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")  # type: ignore[misc]
def test_run_macro_demo_requires_curl(tmp_path: Path) -> None:
    """Script should abort when curl is missing."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    docker_stub = bin_dir / "docker"
    docker_stub.write_text("#!/usr/bin/env bash\nexit 0\n")
    docker_stub.chmod(0o755)

    python_exe = shutil.which("python")
    assert python_exe is not None
    (bin_dir / "python").symlink_to(python_exe)

    env = os.environ.copy()
    env.update({"PATH": str(bin_dir), "DOCKER_LOG": "/dev/null", "CURL_LOG": "/dev/null"})

    result = subprocess.run(
        [f"./{RUN_SCRIPT.name}"],
        cwd=RUN_SCRIPT.parent,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "curl is required" in result.stderr


def test_demo_assets_revision_pinned() -> None:
    expected = "90fe9b623b3a0ae5475cf4fa8693d43cb5ba9ac5"
    with open(RUN_SCRIPT) as f:
        text = f.read()
    m = re.search(r"DEMO_ASSETS_REV=\$\{DEMO_ASSETS_REV:-([0-9a-f]{40})\}", text)
    assert m, "revision variable missing"
    assert m.group(1) == expected

    from alpha_factory_v1.demos.macro_sentinel import data_feeds

    assert data_feeds.DEMO_ASSETS_REV == expected
    for url in data_feeds.OFFLINE_URLS.values():
        assert expected in url
