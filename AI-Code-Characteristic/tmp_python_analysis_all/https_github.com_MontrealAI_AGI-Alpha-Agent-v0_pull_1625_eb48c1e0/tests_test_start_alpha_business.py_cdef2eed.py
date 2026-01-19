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


def test_start_alpha_business_submit_best(monkeypatch) -> None:
    """--submit-best queues the top demo opportunity."""
    from alpha_factory_v1.demos.alpha_agi_business_v1 import start_alpha_business as mod

    class DummyProc:
        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            pass

        def wait(self, timeout: float | None = None) -> None:
            pass

    dummy_proc = DummyProc()
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: dummy_proc)
    monkeypatch.setattr(mod.check_env, "main", lambda *_a, **_k: None)
    monkeypatch.setattr(mod.webbrowser, "open", lambda *_a, **_k: None)

    class Resp:
        def __init__(self) -> None:
            self.status_code = 200

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(mod.requests, "get", lambda *_a, **_k: Resp())
    post_calls: list[tuple] = []

    def fake_post(url: str, json: dict, timeout: int) -> Resp:
        post_calls.append((url, json, timeout))
        return Resp()

    monkeypatch.setattr(mod.requests, "post", fake_post)

    env = {"OPENAI_API_KEY": "", "AGENTS_RUNTIME_PORT": "7000", "PORT": "8000"}
    with monkeypatch.context() as mctx:
        for k, v in env.items():
            mctx.setenv(k, v)
        mod.main(["--no-browser", "--submit-best"])

    assert post_calls == [
        (
            "http://localhost:7000/v1/agents/business_helper/invoke",
            {"action": "best_alpha"},
            10,
        )
    ]
