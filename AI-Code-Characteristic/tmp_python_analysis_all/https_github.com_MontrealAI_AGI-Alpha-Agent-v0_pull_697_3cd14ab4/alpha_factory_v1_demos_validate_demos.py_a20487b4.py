"""Utility to validate demo packages for basic production readiness."""

import os
import sys

DEFAULT_DIR = os.path.dirname(__file__)


def main(base_dir: str = DEFAULT_DIR, min_lines: int = 3, require_code_block: bool = False) -> int:
    """Validate each demo directory for basic production readiness.

    Parameters
    ----------
    base_dir:
        Directory containing all demo sub-packages.
    min_lines:
        Minimum number of lines required in each ``README.md``.
    """
    failures = []
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        if os.path.isdir(path):
            if entry.startswith(".") or entry.startswith("__"):
                continue
            readme = os.path.join(path, "README.md")
            if not os.path.isfile(readme):
                failures.append(f"Missing README.md in {entry}")
            else:
                with open(readme, "r", encoding="utf-8") as fh:
                    lines = fh.readlines()
                if len(lines) < min_lines:
                    failures.append(f"README.md in {entry} too short ({len(lines)} < {min_lines} lines)")
                if not any(line.strip().startswith("#") for line in lines):
                    failures.append(f"README.md in {entry} missing a Markdown heading")
                if require_code_block and not any("```" in line for line in lines):
                    failures.append(f"README.md in {entry} missing fenced code block")
            init_file = os.path.join(path, "__init__.py")
            if not os.path.isfile(init_file):
                failures.append(f"Missing __init__.py in {entry}")

            # Ensure demo contains additional production assets
            visible_files = [
                f for f in os.listdir(path) if not f.startswith(".") and f not in {"README.md", "__init__.py"}
            ]
            if not visible_files:
                failures.append(f"{entry} contains no demo code or assets")
    if failures:
        for msg in failures:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1
    print("All demo directories validated successfully")
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate demo directories")
    parser.add_argument(
        "base_dir",
        nargs="?",
        default=DEFAULT_DIR,
        help="Directory containing demo sub-packages",
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=3,
        help="Minimum number of lines required in each README.md",
    )
    parser.add_argument(
        "--require-code-block",
        action="store_true",
        help="Require each README to include a fenced code block",
    )

    args = parser.parse_args()
    raise SystemExit(
        main(
            base_dir=args.base_dir,
            min_lines=args.min_lines,
            require_code_block=args.require_code_block,
        )
    )
