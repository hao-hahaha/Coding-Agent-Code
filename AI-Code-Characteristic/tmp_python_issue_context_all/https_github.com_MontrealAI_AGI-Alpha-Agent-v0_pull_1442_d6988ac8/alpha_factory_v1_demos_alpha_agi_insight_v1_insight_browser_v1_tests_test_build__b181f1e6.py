# SPDX-License-Identifier: Apache-2.0
"""Test that build.js can execute Python snippets when Python is available."""

import json
import subprocess
from pathlib import Path


def test_python_available() -> None:
    browser_dir = Path(__file__).resolve().parents[1]
    repo_root = browser_dir.parents[3]
    py_snippet = """import ast, json, pathlib
txt = pathlib.Path('scripts/fetch_assets.py').read_text()
tree = ast.parse(txt)
assets = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if getattr(t, 'id', None) == 'ASSETS':
                assets = ast.literal_eval(node.value)
print(json.dumps(list(assets.keys())))"""
    node_code = f"""
import {{ spawnSync }} from 'child_process';
const out = spawnSync('python', ['-'], {{
  input: `{py_snippet}`,
  cwd: {json.dumps(str(repo_root))},
  encoding: 'utf8',
}});
if (out.error) {{ throw out.error; }}
process.exit(out.status);
"""
    res = subprocess.run([
        "node",
        "-e",
        node_code,
    ], cwd=browser_dir, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
