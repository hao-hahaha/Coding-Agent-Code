# SPDX-License-Identifier: Apache-2.0
"""TLS authentication tests for :class:`A2ABus`."""

from __future__ import annotations

import asyncio
import json
import socket
from datetime import datetime, timedelta
from pathlib import Path

import grpc
import pytest

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    HAVE_CRYPTO = True
except Exception:  # pragma: no cover - optional
    HAVE_CRYPTO = False

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.utils import config, messaging


def _free_port() -> int:
    s = socket.socket()
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _make_cert(tmp: Path) -> tuple[str, str, bytes]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=1))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), False)
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    cert_path = tmp / "cert.pem"
    key_path = tmp / "key.pem"
    cert_path.write_bytes(cert_pem)
    key_path.write_bytes(key_pem)
    return str(cert_path), str(key_path), cert_pem


@pytest.mark.skipif(not HAVE_CRYPTO, reason="cryptography not installed")
def test_bus_tls_accept(tmp_path: Path) -> None:
    """Envelope with valid token is accepted over TLS."""
    port = _free_port()
    cert, key, ca = _make_cert(tmp_path)
    cfg = config.Settings(bus_port=port, bus_cert=cert, bus_key=key, bus_token="tok")
    received: list[messaging.Envelope] = []

    async def run() -> None:
        async with messaging.A2ABus(cfg) as bus:
            bus.subscribe("b", lambda e: received.append(e))
            creds = grpc.ssl_channel_credentials(root_certificates=ca)
            async with grpc.aio.secure_channel(f"localhost:{port}", creds) as ch:
                stub = ch.unary_unary("/bus.Bus/Send")
                await stub(f"{messaging.A2ABus.PROTO_VERSION} n1".encode())
                payload = {
                    "sender": "a",
                    "recipient": "b",
                    "payload": {"v": 1},
                    "ts": 0.0,
                    "token": "tok",
                }
                await stub(json.dumps(payload).encode())
            await asyncio.sleep(0.05)

    asyncio.run(run())
    assert received and received[0].payload["v"] == 1


@pytest.mark.skipif(not HAVE_CRYPTO, reason="cryptography not installed")
def test_bus_tls_reject_bad_token(tmp_path: Path) -> None:
    """Invalid token causes rejection."""
    port = _free_port()
    cert, key, ca = _make_cert(tmp_path)
    cfg = config.Settings(bus_port=port, bus_cert=cert, bus_key=key, bus_token="tok")

    async def run() -> None:
        async with messaging.A2ABus(cfg):
            creds = grpc.ssl_channel_credentials(root_certificates=ca)
            async with grpc.aio.secure_channel(f"localhost:{port}", creds) as ch:
                stub = ch.unary_unary("/bus.Bus/Send")
                await stub(f"{messaging.A2ABus.PROTO_VERSION} n2".encode())
                payload = {
                    "sender": "a",
                    "recipient": "b",
                    "payload": {},
                    "ts": 0.0,
                    "token": "bad",
                }
                with pytest.raises(grpc.aio.AioRpcError):
                    await stub(json.dumps(payload).encode())

    asyncio.run(run())
