# SPDX-License-Identifier: Apache-2.0
import subprocess
from pathlib import Path


def test_requires_node_20() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    script = browser_dir / "build.js"
    node_code = (
        "Object.defineProperty(process.versions,'node',{value:'19.0.0'});"
        f" import('./{script.name}')"
    )
    res = subprocess.run(
        ["node", "-e", node_code],
        cwd=browser_dir,
        text=True,
        capture_output=True,
    )
    assert res.returncode == 1
    assert "Node.js 20+ is required. Current version: 19.0.0" in res.stderr

