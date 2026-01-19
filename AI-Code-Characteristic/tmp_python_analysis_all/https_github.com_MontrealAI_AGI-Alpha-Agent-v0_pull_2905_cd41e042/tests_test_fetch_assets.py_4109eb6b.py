# SPDX-License-Identifier: Apache-2.0
import base64
import hashlib
from pathlib import Path
import sys
import pytest
import requests_mock

import scripts.fetch_assets as fa


def test_fetch_assets_failure(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(fa, "ASSETS", {"dummy.txt": "cid"})

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(fa, "download_with_retry", boom)

    with pytest.MonkeyPatch.context() as m:
        m.setattr(sys, "argv", ["fetch_assets.py"])
        with pytest.raises(SystemExit) as exc:
            fa.main()

    _ = capsys.readouterr()
    assert exc.value.code == 1


def test_download_with_retry_fallback(tmp_path: Path, requests_mock: requests_mock.Mocker) -> None:
    path = tmp_path / "out"
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(fa, "FALLBACK_GATEWAYS", ["https://alt.gateway/ipfs"])
    url_primary = f"{fa.GATEWAY}/CID"
    url_alt = "https://alt.gateway/ipfs/CID"
    requests_mock.get(url_primary, status_code=500)
    requests_mock.get(url_alt, text="data")
    try:
        fa.download_with_retry("CID", path, attempts=1)
    finally:
        monkeypatch.undo()
    assert path.read_text() == "data"


def test_verify_assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = b"data"
    asset_path = tmp_path / "file.txt"
    asset_path.write_bytes(content)
    digest = base64.b64encode(hashlib.sha384(content).digest()).decode()
    monkeypatch.setattr(fa, "ASSETS", {"file.txt": "cid"})
    monkeypatch.setattr(fa, "CHECKSUMS", {"file.txt": f"sha384-{digest}"})
    assert fa.verify_assets(tmp_path) == []
    asset_path.write_text("bad")
    assert fa.verify_assets(tmp_path) == ["file.txt"]
