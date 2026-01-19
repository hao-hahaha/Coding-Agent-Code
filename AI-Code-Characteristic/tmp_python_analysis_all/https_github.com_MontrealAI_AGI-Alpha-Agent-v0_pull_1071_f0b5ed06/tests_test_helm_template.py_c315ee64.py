# SPDX-License-Identifier: Apache-2.0
import shutil
import subprocess
from pathlib import Path

import pytest

CHART_DIR = Path(__file__).resolve().parents[1] / "infrastructure" / "helm-chart"
VALUES_FILE = CHART_DIR / "values.example.yaml"

if not shutil.which("helm"):
    pytest.skip("helm not available", allow_module_level=True)


def test_helm_template_renders() -> None:
    subprocess.run(
        ["helm", "template", "alpha-demo", str(CHART_DIR), "-f", str(VALUES_FILE)],
        check=True,
        cwd=CHART_DIR,
        capture_output=True,
        text=True,
    )
