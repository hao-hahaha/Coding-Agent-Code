# SPDX-License-Identifier: Apache-2.0
import shutil
import subprocess
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[1] / "alpha_factory_v1" / "demos" / "macro_sentinel"
COMPOSE_FILE = BASE_DIR / "docker-compose.macro.yml"
RUN_SCRIPT = BASE_DIR / "run_macro_demo.sh"

if not shutil.which("docker"):
    pytest.skip("docker not available", allow_module_level=True)


def test_docker_compose_config() -> None:
    subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE), "config"], check=True, capture_output=True)


def test_run_macro_demo_help() -> None:
    """`run_macro_demo.sh --help` should exit successfully."""
    subprocess.run([str(RUN_SCRIPT), "--help"], check=True, capture_output=True)
