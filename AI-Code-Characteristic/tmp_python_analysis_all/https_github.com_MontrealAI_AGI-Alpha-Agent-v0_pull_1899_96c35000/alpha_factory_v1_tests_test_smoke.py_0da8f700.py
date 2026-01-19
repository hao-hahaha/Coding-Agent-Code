# SPDX-License-Identifier: Apache-2.0
import subprocess
import os
import json
import time
import tempfile
import shutil
import socket
import af_requests as requests
import pathlib
try:
    import pytest
except ModuleNotFoundError:  # pragma: no cover - allow unittest fallback
    class _DummyMark:
        def skipif(self, *_, **__):
            def wrapper(func):
                return func
            return wrapper

    class _DummyPytest:
        mark = _DummyMark()

    pytest = _DummyPytest()  # type: ignore


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

def wait_port(host, port, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket() as s:
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(1)
    raise TimeoutError(f"{host}:{port} not open")

@pytest.mark.skipif(not _docker_available(), reason="docker not available")
def test_container_build_and_ui():
    tmp = tempfile.mkdtemp()
    shutil.copytree(".", tmp, dirs_exist_ok=True)
    img = "af:test"
    subprocess.run(["docker", "build", "-t", img, tmp], check=True)
    cid = subprocess.check_output(["docker", "run", "-d", "-p", "33000:3000", img]).decode().strip()
    try:
        wait_port("localhost", 33000)
        r = requests.get("http://localhost:33000/api/logs")
        assert r.status_code == 200
    finally:
        subprocess.run(["docker", "rm", "-f", cid])


