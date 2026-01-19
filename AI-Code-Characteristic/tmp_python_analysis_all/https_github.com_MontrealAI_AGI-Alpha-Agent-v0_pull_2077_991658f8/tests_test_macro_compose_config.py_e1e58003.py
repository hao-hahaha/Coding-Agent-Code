# SPDX-License-Identifier: Apache-2.0
import shutil
import subprocess
from pathlib import Path

import pytest

COMPOSE_FILE = Path(__file__).resolve().parents[1] / "alpha_factory_v1" / "demos" / "macro_sentinel" / "docker-compose.macro.yml"

if not shutil.which("docker"):
    pytest.skip("docker not available", allow_module_level=True)


def test_docker_compose_config() -> None:
    subprocess.run(["docker", "compose", "-f", str(COMPOSE_FILE), "config"], check=True, capture_output=True)
