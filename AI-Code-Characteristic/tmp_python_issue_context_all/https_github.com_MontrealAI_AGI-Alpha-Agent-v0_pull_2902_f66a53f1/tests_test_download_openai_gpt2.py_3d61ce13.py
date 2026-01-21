# SPDX-License-Identifier: Apache-2.0
import os
from pathlib import Path

import pytest

import scripts.download_openai_gpt2 as dg


def test_model_urls() -> None:
    urls = dg.model_urls("124M")
    prefix = "https://openaipublic.blob.core.windows.net/gpt-2/models/124M/"
    assert urls[0].startswith(prefix)
    assert urls[-1].endswith("vocab.bpe")


@pytest.mark.skipif(os.getenv("PYTEST_NET_OFF") == "1", reason="network disabled")  # type: ignore[misc]
def test_download_invocation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[tuple[str, Path]] = []

    def fake_download(url: str, dest: Path) -> None:
        calls.append((url, dest))
        dest.write_text("stub")

    monkeypatch.setattr(dg, "_download", fake_download)
    dg.download_openai_gpt2("117M", dest=tmp_path)
    assert len(calls) == len(dg._FILE_LIST)
    assert calls[0][0] == dg.model_urls("117M")[0]
