import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Ensure repository root is on the Python path for subprocess execution
REPO_ROOT = Path(__file__).resolve().parents[3]
os.environ.setdefault("PYTHONPATH", str(REPO_ROOT))

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")
uvicorn = pytest.importorskip("uvicorn")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_docs_available() -> None:
    port = _free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    cmd = [
        sys.executable,
        "-m",
        "alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface.api_server",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                r = httpx.get(url + "/docs")
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.1)
        else:
            raise AssertionError("server failed to start")
        assert r.status_code == 200
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
