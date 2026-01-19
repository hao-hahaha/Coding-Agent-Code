# SPDX-License-Identifier: Apache-2.0
"""Test that the MuZero demo script invokes Docker Compose."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path



def test_run_muzero_demo_invokes_docker(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "alpha_factory_v1"
    dst = tmp_path / "alpha_factory_v1"
    shutil.copytree(src, dst)

    script = dst / "demos" / "muzero_planning" / "run_muzero_demo.sh"
    log_file = tmp_path / "docker.log"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker_stub = bin_dir / "docker"
    docker_stub.write_text(
        f"#!/usr/bin/env bash\necho \"$@\" >> '{log_file}'\nexit 0\n"
    )
    docker_stub.chmod(0o755)

    with socket.socket() as s:
        s.bind(("localhost", 0))
        port = s.getsockname()[1]

    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:{env.get('PATH', '')}", "HOST_PORT": str(port)})

    subprocess.run(["bash", str(script)], check=True, env=env)

    assert log_file.read_text(), "Docker stub was not invoked"
    assert "compose" in log_file.read_text()


def test_run_muzero_demo_port_in_use(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "alpha_factory_v1"
    dst = tmp_path / "alpha_factory_v1"
    shutil.copytree(src, dst)

    script = dst / "demos" / "muzero_planning" / "run_muzero_demo.sh"
    log_file = tmp_path / "docker.log"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    docker_stub = bin_dir / "docker"
    docker_stub.write_text(f"#!/usr/bin/env bash\necho docker >> '{log_file}'\nexit 0\n")
    docker_stub.chmod(0o755)

    lsof_stub = bin_dir / "lsof"
    lsof_stub.write_text("#!/usr/bin/env bash\nexit 0\n")
    lsof_stub.chmod(0o755)

    sock = socket.socket()
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]

    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:{env.get('PATH', '')}", "HOST_PORT": str(port)})

    result = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True)
    sock.close()

    assert result.returncode == 1
    assert "already in use" in result.stderr
    assert not log_file.exists() or not log_file.read_text()
