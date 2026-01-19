# SPDX-License-Identifier: Apache-2.0
"""End-to-end test for the static Semgrep gate."""

import os
import shutil
import subprocess
import tempfile

import pytest

SEMGRP_BIN = shutil.which("semgrep")

@pytest.mark.skipif(not SEMGRP_BIN, reason="semgrep not installed")
def test_semgrep_blocks_malicious_diff() -> None:
    bad_sol = """
    contract Bad {
        function attack() public {
            tx.origin;
        }
    }
    """
    with tempfile.NamedTemporaryFile("w", suffix=".sol", delete=False) as fh:
        fh.write(bad_sol)
        path = fh.name
    try:
        result = subprocess.run(
            [SEMGRP_BIN, "--config", "semgrep.yml", path],
            text=True,
            capture_output=True,
        )
        assert result.returncode != 0
    finally:
        os.unlink(path)
