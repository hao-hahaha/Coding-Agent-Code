# SPDX-License-Identifier: Apache-2.0
"""Tests for the JavaScript state serializer."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SERIALIZER = Path(
    "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/src/state/serializer.js"
)


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_js_serializer_roundtrip(tmp_path: Path) -> None:
    script = tmp_path / "run.mjs"
    script.write_text(
        f"import {{save, load}} from '{SERIALIZER.resolve().as_posix()}';\n"
        "const data = JSON.parse(process.argv[2]);\n"
        "const pop = data.pop;\n"
        "if (data.gen !== undefined) pop.gen = data.gen;\n"
        "const out = load(save(pop, data.rngState));\n"
        "console.log(JSON.stringify(out));\n"
    )

    sample = {
        "pop": [
            {"logic": "a", "feasible": True, "front": 0, "strategy": "s"},
            {"logic": "b", "feasible": False, "front": 1, "strategy": "t"},
        ],
        "gen": 5,
        "rngState": [1, 2, 3, 4],
    }

    result = subprocess.run(
        ["node", script, json.dumps(sample)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    loaded = json.loads(result.stdout)
    assert loaded == sample
