#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Generate protobuf modules from ``src/utils/a2a.proto``."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    proto = Path("src/utils/a2a.proto")
    out_dir = proto.parent
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
    dataclass.write_text(
        """# SPDX-License-Identifier: Apache-2.0\n"""
        "\n""\"Dataclass version of ``a2a.proto`` messages.\"\n"""
        "from __future__ import annotations\n"
        "\n"
        "from dataclasses import dataclass, field, asdict\n"
        "from typing import Any, Dict\n"
        "\n\n"
        "@dataclass(slots=True)\n"
        "class Envelope:\n"
        "    \"\"\"Lightweight envelope for bus messages.\"\"\"\n"
        "\n"
        "    sender: str = \"\"\n"
        "    recipient: str = \"\"\n"
        "    payload: Dict[str, Any] = field(default_factory=dict)\n"
        "    ts: float = 0.0\n"
        "\n"
        "    def to_dict(self) -> Dict[str, Any]:\n"
        "        \"\"\"Return a dictionary representation.\"\"\"\n"
        "        return asdict(self)\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
