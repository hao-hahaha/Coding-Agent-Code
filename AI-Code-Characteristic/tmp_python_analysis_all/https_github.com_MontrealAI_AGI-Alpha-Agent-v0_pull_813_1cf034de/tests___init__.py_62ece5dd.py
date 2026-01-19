"""Helper to import the project when not installed."""

from importlib.util import find_spec
from pathlib import Path
import sys

# Allow tests to run from the repository without installing the package
if find_spec("alpha_factory_v1") is None:
    ROOT = Path(__file__).resolve().parents[3]
    if str(ROOT) not in sys.path:
        sys.path.append(str(ROOT))
