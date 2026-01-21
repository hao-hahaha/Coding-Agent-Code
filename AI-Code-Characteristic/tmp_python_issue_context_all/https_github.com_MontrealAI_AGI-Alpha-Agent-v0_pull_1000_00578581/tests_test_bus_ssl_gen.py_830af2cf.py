# SPDX-License-Identifier: Apache-2.0
"""Test TLS envelope delivery using certificates from gen_bus_certs.sh."""

from __future__ import annotations

import asyncio
import json
import socket
import subprocess
import shutil
from pathlib import Path

import grpc
from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging


def _free_port() -> int:
    s = socket.socket()
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _gen_certs(tmp: Path) -> tuple[str, str, bytes, str]:
    root = Path(__file__).resolve().parents[1]
    script = root / "alpha_factory_v1" / "demos" / "alpha_agi_insight_v1" / "infrastructure" / "gen_bus_certs.sh"
    subprocess.run(["bash", str(script)], cwd=tmp, check=True, capture_output=True)
    cert = tmp / "certs" / "bus.crt"
    key = tmp / "certs" / "bus.key"
    token = "change_this_token"
    ca = cert.read_bytes()
    return str(cert), str(key), ca, token


def test_bus_tls_with_script(tmp_path: Path) -> None:
    port = _free_port()
    cert, key, ca, token = _gen_certs(tmp_path)
    cfg = config.Settings(bus_port=port, bus_cert=cert, bus_key=key, bus_token=token)
    bus = messaging.A2ABus(cfg)
    received: list[messaging.Envelope] = []

    async def run() -> None:
        bus.subscribe("b", lambda e: received.append(e))
        await bus.start()
        try:
            creds = grpc.ssl_channel_credentials(root_certificates=ca)
            async with grpc.aio.secure_channel(f"localhost:{port}", creds) as ch:
                stub = ch.unary_unary("/bus.Bus/Send")
                payload = {
                    "sender": "a",
                    "recipient": "b",
                    "payload": {"v": 1},
                    "ts": 0.0,
                    "token": token,
                }
                await stub(json.dumps(payload).encode())
            await asyncio.sleep(0.05)
        finally:
            await bus.stop()
            shutil.rmtree(tmp_path / "certs", ignore_errors=True)

    asyncio.run(run())
    assert received and received[0].payload["v"] == 1
