# SPDX-License-Identifier: Apache-2.0
"""Tests for the Insight WASM bridge."""

import json
import subprocess
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch

from alpha_factory_v1.demos.alpha_agi_insight_v1.src.interface import cli


def _cli_output(seed: int) -> list[dict]:
    with patch.object(cli.orchestrator, "Orchestrator"):
        res = CliRunner().invoke(
            cli.main,
            [
                "simulate",
                "--horizon",
                "1",
                "--offline",
                "--sectors",
                "1",
                "--pop-size",
                "1",
                "--generations",
                "1",
                "--seed",
                str(seed),
                "--curve",
                "linear",
                "--export",
                "json",
            ],
        )
    return json.loads(res.output)


def test_insight_run_matches_cli():
    cli_res = _cli_output(1)
    script = Path(__file__).resolve().parents[1] / "src/wasm/bridge.js"
    node_code = f"""
    import {{ run }} from '{script.as_posix()}';
    global.loadPyodide = async function() {{
      return {{
        runPython: c => require('child_process').spawnSync('python', ['-'], {{input:c,encoding:'utf8'}}).stdout.trim(),
        runPythonAsync: async c => require('child_process').spawnSync('python', ['-'], {{input:c,encoding:'utf8'}}).stdout.trim()
      }};
    }};
    run({{seed:1}}).then(r => console.log(JSON.stringify(r)));
    """
    out = subprocess.run(["node", "-e", node_code], capture_output=True, text=True)
    js_res = json.loads(out.stdout.strip())
    assert js_res == cli_res
