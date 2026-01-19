# SPDX-License-Identifier: Apache-2.0
"""Tests the structuredClone polyfill."""
import shutil
import subprocess
from pathlib import Path

import pytest

CLONE_JS = Path("src/utils/clone.js")

@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_clone_polyfill(tmp_path: Path) -> None:
    script = tmp_path / "run.mjs"
    script.write_text(
        f"globalThis.structuredClone = undefined;\n"
        f"import clone from '{CLONE_JS.resolve().as_posix()}';\n"
        "const src = {a:1,b:{c:2}};\n"
        "const out = clone(src);\n"
        "out.b.c = 3;\n"
        "console.log(src.b.c === 2 && out.b.c === 3);\n",
        encoding="utf-8",
    )
    result = subprocess.run(["node", script], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "true"
