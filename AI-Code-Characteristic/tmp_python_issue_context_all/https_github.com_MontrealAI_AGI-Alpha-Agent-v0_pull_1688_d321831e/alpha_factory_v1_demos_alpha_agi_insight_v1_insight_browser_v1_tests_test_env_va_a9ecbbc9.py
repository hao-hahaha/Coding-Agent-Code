# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "env_var,value,message",
    [
        ("PINNER_TOKEN", " ", "PINNER_TOKEN may not be empty"),
        ("IPFS_GATEWAY", "foo", "Invalid URL in IPFS_GATEWAY"),
    ],
)  # type: ignore[misc]
def test_env_validation_fails(env_var: str, value: str, message: str) -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    script = browser_dir / "build" / "env_validate.js"
    env = os.environ.copy()
    env[env_var] = value
    res = subprocess.run(
        ["node", str(script)],
        cwd=browser_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert message in res.stderr
