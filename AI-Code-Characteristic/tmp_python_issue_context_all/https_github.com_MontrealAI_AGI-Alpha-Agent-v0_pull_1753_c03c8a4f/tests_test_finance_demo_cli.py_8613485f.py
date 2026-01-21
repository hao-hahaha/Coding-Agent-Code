# SPDX-License-Identifier: Apache-2.0
"""Verify the finance demo shell script runs."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def test_finance_demo_cli(tmp_path: Path) -> None:
    script = Path("alpha_factory_v1/demos/finance_alpha/deploy_alpha_factory_demo.sh")
    assert script.exists(), script

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    _write_executable(
        bin_dir / "docker",
        """#!/usr/bin/env bash
if [ "$1" = "image" ]; then exit 0; fi
if [ "$1" = "pull" ]; then exit 0; fi
if [ "$1" = "run" ]; then echo cid123; exit 0; fi
if [ "$1" = "logs" ]; then exit 0; fi
if [ "$1" = "stop" ]; then exit 0; fi
exit 0
""",
    )
    _write_executable(bin_dir / "curl", "#!/usr/bin/env bash\necho '{}'\n")
    _write_executable(bin_dir / "jq", "#!/usr/bin/env bash\ncat >/dev/null\n")
    _write_executable(bin_dir / "lsof", "#!/usr/bin/env bash\nexit 1\n")
    _write_executable(bin_dir / "sleep", "#!/usr/bin/env bash\n[ \"$1\" = \"3600\" ] && exit 1\nexit 0\n")

    env = os.environ.copy()
    env.update({"PATH": f"{bin_dir}:{env.get('PATH', '')}", "PORT_API": "8010", "STRATEGY": "btc_gld"})

    result = subprocess.run(["bash", str(script)], capture_output=True, text=True, env=env, timeout=20)

    assert result.returncode == 0, result.stderr
    assert "Demo complete!" in result.stdout
