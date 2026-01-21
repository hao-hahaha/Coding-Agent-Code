import os
import sys


DEFAULT_DIR = os.path.dirname(__file__)


def main(base_dir: str = DEFAULT_DIR) -> int:
    failures = []
    for entry in os.listdir(base_dir):
        path = os.path.join(base_dir, entry)
        if os.path.isdir(path):
            if entry.startswith('.') or entry.startswith('__'):
                continue
            readme = os.path.join(path, "README.md")
            if not os.path.isfile(readme):
                failures.append(f"Missing README.md in {entry}")
    if failures:
        for msg in failures:
            print(f"ERROR: {msg}", file=sys.stderr)
        return 1
    print("All demo directories contain README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
