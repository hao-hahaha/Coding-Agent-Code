# SPDX-License-Identifier: Apache-2.0
import subprocess
import shutil
import pytest

from src.utils.secure_run import secure_run, SandboxTimeout


def test_secure_run_timeout(monkeypatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda n: None)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=120)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(SandboxTimeout):
        secure_run(["sleep", "130"])
