#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate environment variable documentation.

This script compares the variable names listed in ``alpha_factory_v1/.env.sample``
with the table in ``AGENTS.md``. It exits with a non-zero status if the two sets
of variables differ.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ENV_SAMPLE = ROOT / "alpha_factory_v1" / ".env.sample"
AGENTS_MD = ROOT / "AGENTS.md"


def parse_env_sample(path: Path) -> set[str]:
    vars_set: set[str] = set()
    for line in path.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        var = line.split("=", 1)[0].strip()
        if var:
            vars_set.add(var)
    return vars_set


def parse_agents_table(path: Path) -> set[str]:
    text = path.read_text().splitlines()
    try:
        start = text.index("### Key Environment Variables")
    except ValueError:
        return set()

    table_vars: set[str] = set()
    for line in text[start + 1 :]:
        if line.startswith("|"):
            match = re.search(r"`([^`]+)`", line)
            if match:
                table_vars.add(match.group(1))
            continue
        if table_vars:
            break
    return table_vars


def main() -> int:
    env_vars = parse_env_sample(ENV_SAMPLE)
    md_vars = parse_agents_table(AGENTS_MD)

    missing_in_md = sorted(env_vars - md_vars)
    missing_in_env = sorted(md_vars - env_vars)

    if missing_in_md or missing_in_env:
        if missing_in_md:
            print("Missing from AGENTS.md:", ", ".join(missing_in_md))
        if missing_in_env:
            print("Missing from .env.sample:", ", ".join(missing_in_env))
        return 1

    print("Environment variable table is up-to-date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
