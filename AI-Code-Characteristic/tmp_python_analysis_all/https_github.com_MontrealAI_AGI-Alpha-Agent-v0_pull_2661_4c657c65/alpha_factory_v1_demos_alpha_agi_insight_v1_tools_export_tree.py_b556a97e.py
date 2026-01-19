#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Export a meta-agent run to a visualization tree.

The script reads JSONL logs produced during a meta-agent run and
converts them into the hierarchical ``tree.json`` format used by the
Insight browser demo. Each log line must contain a ``path`` array and a
numeric ``score`` field. The highest scoring path is stored under the
``bestPath`` key in the output.

Example:
    python export_tree.py lineage/run.jsonl -o docs/alpha_agi_insight_v1/tree.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _add_path(root: Dict[str, Any], path: Iterable[str]) -> None:
    node = root
    for name in path:
        children = node.setdefault("children", [])
        for child in children:
            if child.get("name") == name:
                node = child
                break
        else:
            child = {"name": name}
            children.append(child)
            node = child


def _build_tree(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    tree: Dict[str, Any] = {"name": "Start", "children": []}
    best_score = float("-inf")
    best_path: List[str] = []
    for rec in records:
        path = rec.get("path")
        if not isinstance(path, list):
            continue
        score = float(rec.get("score", 0))
        _add_path(tree, path)
        if score > best_score:
            best_score = score
            best_path = ["Start"] + path
    tree["bestPath"] = best_path
    return tree


def _read_logs(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for p in paths:
        with p.open(encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def main() -> None:
    ap = argparse.ArgumentParser(description="Export tree visualization data")
    ap.add_argument("logs", type=Path, nargs="+", help="JSONL log files")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("tree.json"),
        help="Destination JSON path",
    )
    args = ap.parse_args()

    recs = _read_logs(args.logs)
    tree = _build_tree(recs)
    args.output.write_text(json.dumps(tree, indent=2))
    print(f"Tree exported → {args.output}")


if __name__ == "__main__":  # pragma: no cover
    main()
