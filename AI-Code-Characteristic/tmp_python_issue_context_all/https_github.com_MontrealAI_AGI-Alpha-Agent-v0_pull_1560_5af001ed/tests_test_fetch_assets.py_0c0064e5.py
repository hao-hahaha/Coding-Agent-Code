# SPDX-License-Identifier: Apache-2.0
import pytest

import scripts.fetch_assets as fa


def test_fetch_assets_failure(monkeypatch, capsys):
    monkeypatch.setattr(fa, "ASSETS", {"dummy.txt": "cid"})

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(fa, "download_with_retry", boom)

    with pytest.raises(SystemExit) as exc:
        fa.main()

    out = capsys.readouterr().out
    assert "Download failed for dummy.txt" in out
    assert "ERROR: Unable to retrieve dummy.txt" in out
    assert exc.value.code == 1
