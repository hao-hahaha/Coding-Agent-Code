# SPDX-License-Identifier: Apache-2.0
"""Tests for the Macro-Sentinel run script."""

from __future__ import annotations

import os
import shutil
import subprocess
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
        "echo \"$@\" >> \"$DOCKER_LOG\"\n"
        "if [ \"$1\" = \"info\" ]; then echo \"{}\"; fi\n"
        "if [ \"$1\" = \"version\" ]; then echo \"24.0.0\"; fi\n"
        "exit 0\n"
    )
    docker_stub.chmod(0o755)

    curl_stub = bin_dir / "curl"
    curl_stub.write_text(
        "#!/usr/bin/env bash\n"
        "echo \"$@\" >> \"$CURL_LOG\"\n"
        f"exit {curl_rc}\n"
    )
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


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")
def test_run_macro_demo_no_offline(tmp_path: Path) -> None:
    """`OPENAI_API_KEY` disables the offline profile."""
    docker_log, _ = _run_script(tmp_path, env={"OPENAI_API_KEY": "dummy-key"})
    assert "--profile offline" not in docker_log


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")
def test_run_macro_demo_health_check(tmp_path: Path) -> None:
    """Health gate should hit the expected endpoint."""
    _, curl_log = _run_script(tmp_path, env={"OPENAI_API_KEY": "dummy-key"})
    assert "http://localhost:7864/healthz" in curl_log


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")
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


@pytest.mark.skipif(not RUN_SCRIPT.exists(), reason="script missing")
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
