#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Create `config.env` for the Alpha-AGI Business demo."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def ensure_config(directory: Path) -> tuple[Path, bool]:
    """Ensure ``config.env`` exists in ``directory``.

    Returns the path and whether it was created.
    """
    config = directory / "config.env"
    if config.exists():
        return config, False
    sample = directory / "config.env.sample"
    shutil.copyfile(sample, config)
    return config, True


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create config.env if missing")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Demo directory (default: parent of this script)",
    )
    args = parser.parse_args(argv)
    path, created = ensure_config(args.dir)
    if created:
        print(f"Created {path}. Edit this file to set secrets.")
    else:
        print(f"{path} already exists. Edit it to update secrets.")


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
