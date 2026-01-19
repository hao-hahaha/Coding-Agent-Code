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

    dataclass = out_dir / "a2a_pb2_dataclass.py"

    if HAS_GRPC and shutil.which("protoc-gen-python_betterproto"):
        with tempfile.TemporaryDirectory() as tmp:
            better_cmd = [
                sys.executable,
                "-m",
                "grpc_tools.protoc",
                f"-I{out_dir}",
                f"--python_betterproto_out={tmp}",
                str(proto),
            ]
            if subprocess.run(better_cmd, check=False).returncode == 0:
                generated = Path(tmp) / "a2a_pb.py"
                if not generated.exists():
                    generated = Path(tmp) / "a2a_pb2.py"
                if generated.exists():
                    dataclass.write_text(generated.read_text())
                    return 0

    dataclass.write_text(
        '''# SPDX-License-Identifier: Apache-2.0

Dataclass version of ``a2a.proto`` messages.

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict


@dataclass(slots=True)
class Envelope:
    """Lightweight envelope for bus messages."""

    sender: str = ""
    recipient: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    ts: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation."""
        return asdict(self)
'''
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
