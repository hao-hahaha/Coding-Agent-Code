import subprocess
import sys

def test_edge_runner_help():
    result = subprocess.run(
        [sys.executable, '-m', 'alpha_factory_v1.edge_runner', '--help'],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert 'usage' in result.stdout.lower()
