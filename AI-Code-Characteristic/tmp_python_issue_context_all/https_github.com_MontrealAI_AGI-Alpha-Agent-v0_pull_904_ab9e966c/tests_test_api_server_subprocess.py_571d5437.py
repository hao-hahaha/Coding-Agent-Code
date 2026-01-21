import os
import socket
import subprocess
import sys
import time

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

os.environ.setdefault("API_TOKEN", "test-token")
os.environ.setdefault("API_RATE_LIMIT", "1000")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_simulate_curve_subprocess() -> None:
    port = _free_port()
    env = os.environ.copy()
    cmd = [
        sys.executable,
        "-m",
        "src.interface.api_server",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    proc = subprocess.Popen(cmd, env=env)
    url = f"http://127.0.0.1:{port}"
    headers = {"Authorization": "Bearer test-token"}
    try:
        for _ in range(50):
            try:
                r = httpx.get(f"{url}/runs", headers=headers)
                if r.status_code == 200:
                    break
            except Exception:
                time.sleep(0.1)
        else:
            proc.terminate()
            raise AssertionError("server did not start")
        r = httpx.post(
            f"{url}/simulate",
            json={"horizon": 1, "pop_size": 2, "generations": 1, "curve": "linear"},
            headers=headers,
        )
        assert r.status_code == 200
        sim_id = r.json()["id"]
        for _ in range(400):
            r = httpx.get(f"{url}/results/{sim_id}", headers=headers)
            if r.status_code == 200:
                break
            time.sleep(0.05)
        assert r.status_code == 200
    finally:
        proc.terminate()
        proc.wait(timeout=5)
