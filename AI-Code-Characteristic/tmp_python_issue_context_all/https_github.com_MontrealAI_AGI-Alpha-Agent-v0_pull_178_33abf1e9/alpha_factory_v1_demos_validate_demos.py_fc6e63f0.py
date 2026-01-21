import os
import sys


DEFAULT_DIR = os.path.dirname(__file__)


def main(base_dir: str = DEFAULT_DIR, min_lines: int = 3) -> int:
    """Validate that each demo directory contains a sufficiently detailed README."""
    failures = []
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        if os.path.isdir(path):
            if entry.startswith('.') or entry.startswith('__'):
                continue
            readme = os.path.join(path, "README.md")
            if not os.path.isfile(readme):
                failures.append(f"Missing README.md in {entry}")
            else:
                with open(readme, "r", encoding="utf-8") as fh:
                    lines = sum(1 for _ in fh)
                if lines < min_lines:
                    failures.append(
                        f"README.md in {entry} too short ({lines} < {min_lines} lines)"
                    )
    if failures:
        for msg in failures:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1
    print("All demo directories contain a sufficiently detailed README")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
