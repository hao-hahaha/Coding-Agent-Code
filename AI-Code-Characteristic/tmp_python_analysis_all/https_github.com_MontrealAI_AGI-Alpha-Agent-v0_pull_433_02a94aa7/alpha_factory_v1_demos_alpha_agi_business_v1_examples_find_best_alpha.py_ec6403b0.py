import json
from pathlib import Path
import sys


def main() -> None:
    """Print the highest scoring alpha opportunity."""
    path = Path(__file__).with_name("alpha_opportunities.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error: The file '{path}' was not found.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when trying to read the file '{path}'.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from the file '{path}'. Please check the file's contents.")
        sys.exit(1)
    best = max(data, key=lambda x: x.get("score", 0))
    print("Best alpha opportunity:")
    print(f"  description: {best['alpha']}")
    print(f"  score: {best['score']}")


if __name__ == "__main__":
    main()
