"""Light-weight dependency check for demos and tests.

This helper validates that the Python packages required by the
Alpha‑Factory demos and unit tests are present.  When invoked with the
``--auto-install`` flag (or ``AUTO_INSTALL_MISSING=1`` environment
variable) it attempts to install any missing dependencies using
``pip``.  For air‑gapped environments supply ``--wheelhouse`` or set
``WHEELHOUSE=/path/to/wheels`` so ``pip`` can resolve packages from a
local directory.

The script prints a warning when packages are missing but continues to
run so the demos remain usable in restricted setups.
"""

import importlib.util
import subprocess
import os
import sys
import argparse
from typing import List, Optional

REQUIRED = [
    "pytest",
    "prometheus_client",
    "openai",
    "anthropic",
    "fastapi",
    "opentelemetry",
]

# Optional integrations that may not be present in restricted environments.
OPTIONAL = [
    "openai_agents",
    "google_adk",
]

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate runtime dependencies")
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Attempt pip install of any missing packages",
    )
    parser.add_argument(
        "--wheelhouse",
        help="Optional path to a local wheelhouse for offline installs",
    )

    args = parser.parse_args(argv)

    missing_required: list[str] = []
    missing_optional: list[str] = []
    for pkg in REQUIRED + OPTIONAL:
        try:
            spec = importlib.util.find_spec(pkg)
        except ValueError:
            # handle cases where a namespace package left an invalid entry
            spec = None
        if spec is None:
            if pkg in OPTIONAL:
                missing_optional.append(pkg)
            else:
                missing_required.append(pkg)
    missing = missing_required + missing_optional
    if missing:
        print("WARNING: Missing packages:", ", ".join(missing))
        wheelhouse = args.wheelhouse or os.getenv("WHEELHOUSE")
        auto = args.auto_install or os.getenv("AUTO_INSTALL_MISSING") == "1"
        if auto:
            cmd = [sys.executable, "-m", "pip", "install", "--quiet"]
            if wheelhouse:
                cmd += ["--no-index", "--find-links", wheelhouse]
            cmd += missing
            print("Attempting automatic install:", " ".join(cmd))
            rc = subprocess.call(cmd)
            if rc != 0:
                print("Automatic install failed with code", rc)
            else:
                print("Install completed, verifying …")
                missing = [p for p in missing if importlib.util.find_spec(p) is None]
                missing_required = [p for p in missing if p not in OPTIONAL]
                if missing_required:
                    print("ERROR: The following packages are still missing after the installation attempt:", ", ".join(missing_required))
                    return 1
        else:
            hint = "pip install " + " ".join(missing)
            if wheelhouse:
                hint = f"pip install --no-index --find-links {wheelhouse} " + " ".join(missing)
            print("Some features may be degraded. Install with:", hint)

    if not missing_required:
        print("Environment OK")
    return 0

if __name__ == '__main__':
    sys.exit(main())
