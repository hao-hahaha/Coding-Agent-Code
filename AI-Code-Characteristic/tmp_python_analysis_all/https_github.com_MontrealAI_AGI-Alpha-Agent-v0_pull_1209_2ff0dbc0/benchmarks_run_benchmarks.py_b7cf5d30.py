#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Run benchmark tasks and emit JSON results."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from time import perf_counter_ns

ROOT = Path(__file__).parent

def _discover_tasks(dataset: str) -> list[tuple[str, str]]:
    """Return list of (task_id, module_name)."""
    tasks = []
    base = ROOT.parent
    for path in (ROOT / dataset).glob("task_*.py"):
        rel = path.with_suffix("").relative_to(base)
        module_name = ".".join(rel.parts)
        task_id = f"{dataset}/{path.stem}"
        tasks.append((task_id, module_name))
    return tasks

def run_task(task_id: str, module_name: str) -> dict[str, object]:
    t0 = perf_counter_ns()
    passed = True
    try:
        mod = importlib.import_module(module_name)
        if hasattr(mod, "run"):
            mod.run()
    except Exception:
        passed = False
    elapsed_ms = int((perf_counter_ns() - t0) / 1_000_000)
    return {"task_id": task_id, "pass": passed, "time_ms": elapsed_ms}

def main() -> None:
    # Ensure the repository root is on sys.path so benchmark modules import
    sys.path.insert(0, str(ROOT.parent))
    datasets = [
        "swebench_verified_mini",
        "polyglot_lite",
        "swe_mini",
        "poly_mini",
    ]
    results = []
    for ds in datasets:
        for task_id, module in _discover_tasks(ds):
            results.append(run_task(task_id, module))
    json.dump(results, sys.stdout)

if __name__ == "__main__":  # pragma: no cover
    main()
