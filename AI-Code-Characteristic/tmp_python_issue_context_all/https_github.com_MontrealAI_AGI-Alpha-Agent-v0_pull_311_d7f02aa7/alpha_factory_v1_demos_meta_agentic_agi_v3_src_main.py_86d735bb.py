import sys
from pathlib import Path


def main() -> None:
    """Entry-point for Meta-Agentic AGI v3 demo."""
    pkg_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(pkg_dir))
    from meta_agentic_agi_demo_v3 import main as demo_main
    demo_main()


if __name__ == "__main__":
    main()
