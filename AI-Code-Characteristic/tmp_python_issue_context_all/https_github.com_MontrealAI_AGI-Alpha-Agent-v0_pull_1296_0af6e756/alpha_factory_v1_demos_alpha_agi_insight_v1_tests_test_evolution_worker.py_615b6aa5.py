# SPDX-License-Identifier: Apache-2.0
"""Regression tests for the evolution worker."""
import io
import sys
import tarfile
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))


def _make_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path))
    from alpha_factory_v1.demos.alpha_agi_insight_v1.src import evolution_worker

    return TestClient(evolution_worker.app)


def _make_tar(member: tarfile.TarInfo) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(mode="w", fileobj=buf) as tf:
        tf.addfile(member)
    return buf.getvalue()


def test_rejects_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(tmp_path, monkeypatch)

    info = tarfile.TarInfo("link")
    info.type = tarfile.SYMTYPE
    info.linkname = "../evil"
    payload = _make_tar(info)

    resp = client.post("/mutate", files={"tar": ("bad.tar", payload, "application/x-tar")})
    assert resp.status_code == 400


def test_rejects_absolute_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client(tmp_path, monkeypatch)

    info = tarfile.TarInfo("/abs.txt")
    info.size = 0
    payload = _make_tar(info)

    resp = client.post("/mutate", files={"tar": ("bad.tar", payload, "application/x-tar")})
    assert resp.status_code == 400
