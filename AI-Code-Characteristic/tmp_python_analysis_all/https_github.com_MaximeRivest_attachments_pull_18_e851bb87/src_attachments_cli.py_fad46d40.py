#!/usr/bin/env python3
"""Command line interface for the attachments library."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Union

from . import Attachments, adapt, set_verbose


def _build_dsl(extra_args: List[str]) -> str:
    """Convert unknown CLI options to DSL fragment."""
    dsl_map: Dict[str, Union[str, List[str]]] = {}
    i = 0
    while i < len(extra_args):
        token = extra_args[i]
        if token.startswith("--"):
            key = token[2:]
            value = "true"
            if "=" in key:
                key, value = key.split("=", 1)
            elif i + 1 < len(extra_args) and not extra_args[i + 1].startswith("--"):
                value = extra_args[i + 1]
                i += 1
            existing = dsl_map.get(key)
            if existing is None:
                dsl_map[key] = value
            else:
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    dsl_map[key] = [existing, value]
        i += 1

    parts = []
    for key, value in dsl_map.items():
        if isinstance(value, list):
            value = ",".join(value)
        parts.append(f"[{key}:{value}]")
    return "".join(parts)


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Process files with Attachments DSL")
    parser.add_argument("paths", nargs="*", help="Files, URLs or directories to process")
    parser.add_argument("-c", "--cwd", help="Change working directory before processing")
    parser.add_argument("-q", "--quiet", action="store_true", help="Silence verbose logs")
    parser.add_argument(
        "-y",
        "--copy",
        action="store_true",
        help="Copy result text to clipboard using to_clipboard_text",
    )
    parser.add_argument("--prompt", default="", help="Prompt when copying to clipboard")

    args, extra = parser.parse_known_args(argv)

    if args.cwd:
        os.chdir(args.cwd)

    set_verbose(not args.quiet)

    dsl_fragment = _build_dsl(extra)
    paths = args.paths or ["."]
    paths_with_dsl = [p + dsl_fragment for p in paths]

    try:
        ctx = Attachments(*paths_with_dsl)
        if args.copy:
            adapt.to_clipboard_text(ctx, prompt=args.prompt)
        else:
            output = str(ctx)
            if output:
                print(output)
    except Exception as exc:
        print(f"Error running attachments CLI: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
