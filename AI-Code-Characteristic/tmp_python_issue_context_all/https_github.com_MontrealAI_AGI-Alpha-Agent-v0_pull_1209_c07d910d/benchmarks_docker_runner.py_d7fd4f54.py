#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Run benchmarks inside Docker and enforce runtime limit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parent
IMAGE = "python:3.11-slim"


def _run_container() -> str:
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{ROOT.parent}:/work",
        "-w",
        "/work",
        IMAGE,
        "python",
        "benchmarks/run_benchmarks.py",
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout


def main() -> None:
    t0 = perf_counter_ns()
    out = _run_container()
    elapsed_ms = int((perf_counter_ns() - t0) / 1_000_000)
    data = json.loads(out)
    json.dump(data, sys.stdout)
    sys.stdout.write("\n")
    avg_ms = sum(d["time_ms"] for d in data) / len(data)
    if avg_ms > 300_000:  # 5 minutes
        raise SystemExit(
            f"Average runtime {avg_ms/1000:.1f}s exceeds 5 minute limit (total {elapsed_ms/1000:.1f}s)"
        )


if __name__ == "__main__":  # pragma: no cover
    main()
