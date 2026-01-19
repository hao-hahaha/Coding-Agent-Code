#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Generate protobuf modules from ``src/utils/a2a.proto``."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import shutil
import tempfile

try:  # optional dependency
    import grpc_tools.protoc  # noqa: F401
    HAS_GRPC = True
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    HAS_GRPC = False


def main() -> int:
    proto = Path("src/utils/a2a.proto")
    out_dir = proto.parent
    if HAS_GRPC:
        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{out_dir}",
            f"--python_out={out_dir}",
            str(proto),
        ]
        if subprocess.run(cmd, check=False).returncode != 0:
            return 1

    go_out = Path("alpha_factory_v1/proto/go")
    go_out.mkdir(parents=True, exist_ok=True)

    if shutil.which("protoc") and shutil.which("protoc-gen-go"):
        go_cmd = [
            "protoc",
            f"-I{out_dir}",
            f"--go_out={go_out}",
            "--go_opt=paths=source_relative",
            str(proto),
        ]
        subprocess.run(go_cmd, check=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
