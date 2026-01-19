# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_start_alpha_business_no_browser() -> None:
    script = Path("alpha_factory_v1/demos/alpha_agi_business_v1/start_alpha_business.py")
    port = _free_port()
    runtime_port = _free_port()
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = ""
    env["AGENTS_RUNTIME_PORT"] = str(runtime_port)
    env["PORT"] = str(port)
    env.setdefault("API_TOKEN", "demo-token")
    proc = subprocess.Popen([sys.executable, str(script), "--no-browser"], env=env)
    try:
        time.sleep(2)
        assert proc.poll() is None
    finally:
        proc.terminate()
        proc.wait(timeout=5)
