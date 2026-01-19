# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
import shutil
import tempfile
from pathlib import Path

import pytest

TERRAFORM_DIR = (
    Path(__file__).resolve().parents[1]
    / "alpha_factory_v1"
    / "demos"
    / "alpha_agi_insight_v1"
    / "infrastructure"
    / "terraform"
)
FILES = ["main_gcp.tf", "main_aws.tf"]

if not shutil.which("terraform"):
    pytest.skip("terraform not available", allow_module_level=True)


@pytest.mark.parametrize("tf_file", FILES)
def test_demo_terraform_validate(tf_file: str) -> None:
    env = os.environ.copy()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        shutil.copy(TERRAFORM_DIR / tf_file, tmp_path / tf_file)
        subprocess.run(
            ["terraform", "init", "-backend=false", "-input=false"],
            cwd=tmp_path,
            check=True,
            env=env,
        )
        subprocess.run(
            ["terraform", "validate", "-no-color"],
            cwd=tmp_path,
            check=True,
            env=env,
        )
