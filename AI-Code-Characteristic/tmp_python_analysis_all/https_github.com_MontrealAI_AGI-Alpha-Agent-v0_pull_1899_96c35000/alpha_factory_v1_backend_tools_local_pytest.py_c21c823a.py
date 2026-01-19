# SPDX-License-Identifier: Apache-2.0
"""
backend/tools/local_pytest.py
─────────────────────────────
Production-grade **FunctionTool** that runs *pytest* inside a tightly
sandboxed subprocess so agents can evaluate a codebase safely.

Key features
============
• **SDK-agnostic** – works even if `openai-agents` is not installed.
• **Cross-platform** – gracefully handles missing `resource` on Windows.
• **Hardened sandbox** – CPU-seconds + memory cap + (optional) network off.
• **Deterministic output** – normalised JSON payload for easy tool-chaining.
• **No external dependencies** – only stdlib + (optional) agents SDK.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
import shutil
from pathlib import Path
from typing import Any, Dict

# ───────────────────────────────────────────────────────────────────────────
# Optional import – the file still works if the OpenAI Agents SDK is absent
# (for instance when a user runs with no OPENAI_API_KEY and only local tools).
# ───────────────────────────────────────────────────────────────────────────
try:  # pragma: no cover - optional dependency
    # OpenAI Agents SDK ≥ 0.0.13
    from agents import function_tool, RunContextWrapper  # type: ignore
    _HAVE_AGENTS = True
except ModuleNotFoundError:  # pragma: no cover
    # Provide minimal fallbacks so the orchestrator can import the module.
    def function_tool(*_dargs, **_dkwargs):  # noqa: D401
        """Decorator-no-op fallback when Agents SDK is missing."""

        def _inner(fn):  # type: ignore
            return fn

        return _inner

    RunContextWrapper = Dict  # type: ignore
    _HAVE_AGENTS = False

# ───────────────────────────────────────────────────────────────────────────
# Sandbox / resource limits
# ───────────────────────────────────────────────────────────────────────────
CPU_SOFT_SEC = int(os.getenv("PYTEST_CPU_SOFT_SEC", "5"))
CPU_HARD_SEC = CPU_SOFT_SEC + 1  # kill grace window
MEM_CAP_MB = int(os.getenv("PYTEST_MEM_MB", "256"))
NETWORK_OFF = os.getenv("PYTEST_NET_OFF", "1") == "1"

_IS_POSIX = os.name == "posix"
_IS_WINDOWS = platform.system() == "Windows"


def _apply_rlimits() -> None:  # pragma: no cover – platform specific
    """Apply CPU & memory caps (POSIX only)."""
    if not _IS_POSIX:
        return
    import resource  # pylint: disable=import-error

    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SOFT_SEC, CPU_HARD_SEC))
    # Convert MB → Bytes
    mem_bytes = MEM_CAP_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))


# ───────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────
def _strip_ansi(text: str) -> str:
    """Remove ANSI colour codes (keeps JSON payload clean)."""
    import re

    ansi_escape = re.compile(r"\x1b\[[0-9;]*[mK]")
    return ansi_escape.sub("", text)


def _build_env() -> Dict[str, str]:
    """Return a sanitized environment for the child pytest process."""
    env = os.environ.copy()

    if NETWORK_OFF and _IS_POSIX:
        # Use the `unshare`/`nsenter` trick if available to drop network.
        # If tools like `firejail` are present the user can export
        # PYTEST_NET_OFF=0 to disable.
        env["PYTHONHTTPSVERIFY"] = "0"  # mitigate SSL noise inside ns

    # Remove variables that could leak credentials into the sandboxed tests
    for key in list(env):
        if key.upper().endswith(("TOKEN", "SECRET", "PASSWORD", "KEY")):
            env.pop(key, None)

    return env


def _run_pytest(path: Path) -> Dict[str, Any]:
    """Execute pytest under the configured sandbox & return a JSONable dict."""
    start = time.perf_counter()

    cmd = [sys.executable, "-m", "pytest", "-q", str(path)]
    # On POSIX, optionally drop network using `unshare`.
    if NETWORK_OFF and _IS_POSIX and shutil.which("unshare"):  # type: ignore
        cmd = ["unshare", "--net"] + cmd

    # Windows lacks RLIMIT, but we still run pytest without caps.
    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        cwd=str(path),
        env=_build_env(),
        preexec_fn=_apply_rlimits if _IS_POSIX else None,
    )

    end = time.perf_counter()
    duration = round(end - start, 3)

    return {
        "returncode": proc.returncode,
        "passed": proc.returncode == 0,
        "duration_sec": duration,
        "stdout": _strip_ansi(proc.stdout),
        "stderr": _strip_ansi(proc.stderr),
        "cmd": " ".join(cmd),
    }


# ───────────────────────────────────────────────────────────────────────────
# Public tool – registered with the Agents SDK when available
# ───────────────────────────────────────────────────────────────────────────
def run_pytest_impl(
    ctx: RunContextWrapper | Dict,  # SDK passes full RunContextWrapper
    path: str = ".",
) -> Dict[str, Any]:
    """
    Execute *pytest* in a hardened sandbox.

    Parameters
    ----------
    ctx:
        The caller context object (unused but part of FunctionTool signature).
    path:
        Directory or test file pattern to run.  Defaults to current working dir.

    Returns
    -------
    dict
        {
            "returncode": int,
            "passed": bool,
            "duration_sec": float,
            "stdout": "…",
            "stderr": "…",
            "cmd": "python -m pytest …"
        }
    """
    repo_path = Path(path).expanduser().resolve()
    if not repo_path.exists():
        return {
            "returncode": -1,
            "passed": False,
            "duration_sec": 0,
            "stdout": "",
            "stderr": f"Path not found: {repo_path}",
            "cmd": "",
        }

    result = _run_pytest(repo_path)

    # Agents SDK expects serialisable output (no pathlib, bytes, etc.)
    return json.loads(json.dumps(result, ensure_ascii=False))


if _HAVE_AGENTS:
    run_pytest_tool = function_tool(
        name_override="run_pytest",
        description_override=(
            "Run pytest on the specified directory or file under strict "
            "resource limits (default: current repo). Returns JSON with "
            "returncode, stdout, stderr, and timing."
        ),
        strict_mode=False,
    )(run_pytest_impl)
else:  # pragma: no cover - offline fallback
    run_pytest_tool = run_pytest_impl

# Backwards-compatible public alias
run_pytest = run_pytest_impl


# Ensure a clean public namespace
__all__ = ["run_pytest", "run_pytest_tool"]
