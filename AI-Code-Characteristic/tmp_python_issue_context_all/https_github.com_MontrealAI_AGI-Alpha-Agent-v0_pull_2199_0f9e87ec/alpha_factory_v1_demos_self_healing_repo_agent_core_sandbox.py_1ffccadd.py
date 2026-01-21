# SPDX-License-Identifier: Apache-2.0
"""Minimal Docker wrapper for sandboxed execution."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Iterable, Mapping

DEFAULT_IMAGE = os.getenv("SANDBOX_IMAGE", "python:3.11-slim")


def run_in_docker(
    command: Iterable[str],
    repo_dir: str,
    *,
    image: str | None = None,
    mounts: Mapping[str, str] | None = None,
) -> tuple[int, str]:
    """Execute ``command`` inside ``image`` with ``repo_dir`` mounted.

    Additional ``mounts`` map host paths to container paths.
    Returns the exit code and combined stdout+stderr.
    """

    image = image or DEFAULT_IMAGE
    if not shutil.which("docker"):
        raise RuntimeError("docker is required to run the sandbox")
    mounts = mounts or {}
    cmd = [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "-v",
        f"{repo_dir}:/app",
    ]
    for host, target in mounts.items():
        cmd += ["-v", f"{host}:{target}"]
    cmd += ["-w", "/app", image, *command]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, (result.stdout or "") + (result.stderr or "")

