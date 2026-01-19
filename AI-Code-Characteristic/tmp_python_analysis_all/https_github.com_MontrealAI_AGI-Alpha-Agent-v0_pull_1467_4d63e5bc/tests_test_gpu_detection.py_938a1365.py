# SPDX-License-Identifier: Apache-2.0
import shutil
import subprocess
from pathlib import Path
import pytest

LLM = Path(
    "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/src/utils/llm.js"
)

@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_llm_gpu_backend(tmp_path: Path) -> None:
    script = tmp_path / "run.mjs"
    script.write_text(
        f"globalThis.navigator = {{ gpu: {{}} }};\n"
        f"globalThis.localStorage = {{ getItem: () => null }};\n"
        f"const m = await import('{LLM.resolve().as_posix()}');\n"
        "console.log(m.gpuBackend());\n"
    )
    res = subprocess.run(["node", script], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == "webgpu"


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_llm_no_gpu_backend(tmp_path: Path) -> None:
    script = tmp_path / "run.mjs"
    script.write_text(
        f"globalThis.navigator = {{}};\n"
        f"globalThis.localStorage = {{ getItem: () => null }};\n"
        f"const m = await import('{LLM.resolve().as_posix()}');\n"
        "console.log(m.gpuBackend());\n"
    )
    res = subprocess.run(["node", script], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == "wasm-simd"
