# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the consilience calculation."""

import json
import shutil
import subprocess
from pathlib import Path
import pytest

CRITICS = Path(
    "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/src/wasm/critics.js"
)


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_consilience_values(tmp_path: Path) -> None:
    script = tmp_path / "run.mjs"
    script.write_text(
        f"import {{ consilience }} from '{CRITICS.resolve().as_posix()}';\n"
        "const r1 = consilience({a:0.5,b:0.5,c:0.5});\n"
        "const r2 = consilience({a:0,b:1});\n"
        "console.log(JSON.stringify({r1,r2}));\n"
    )
    result = subprocess.run(["node", script], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    assert data["r1"] > 0.99
    assert data["r2"] < data["r1"]
