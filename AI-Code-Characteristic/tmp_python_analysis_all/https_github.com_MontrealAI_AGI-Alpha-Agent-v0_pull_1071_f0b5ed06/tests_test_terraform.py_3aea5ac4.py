# SPDX-License-Identifier: Apache-2.0
import os
import subprocess
import shutil
from pathlib import Path

import pytest

TERRAFORM_DIR = Path(__file__).resolve().parents[1] / "infrastructure" / "terraform"

if not shutil.which("terraform"):
    pytest.skip("terraform not available", allow_module_level=True)


def test_terraform_validate() -> None:
    env = os.environ.copy()
    subprocess.run(
        ["terraform", "init", "-backend=false", "-input=false"],
        cwd=TERRAFORM_DIR,
        check=True,
        env=env,
    )
    subprocess.run(
        ["terraform", "validate", "-no-color"],
        cwd=TERRAFORM_DIR,
        check=True,
        env=env,
    )
