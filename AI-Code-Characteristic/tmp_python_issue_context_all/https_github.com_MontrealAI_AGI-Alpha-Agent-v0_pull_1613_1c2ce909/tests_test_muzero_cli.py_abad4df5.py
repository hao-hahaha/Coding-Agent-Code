# SPDX-License-Identifier: Apache-2.0
import subprocess
import sys


def test_cli_help() -> None:
    result = subprocess.run([
        sys.executable,
        '-m', 'alpha_factory_v1.demos.muzero_planning',
        '--help'
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert 'MuZero planning demo' in result.stdout
