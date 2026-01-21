"""Light-weight dependency check for demos and tests."""

import importlib.util
import subprocess
import os
import sys
import argparse

REQUIRED = [
    "pytest",
    "prometheus_client",
    "openai",
    "openai_agents",
    "google_adk",
    "anthropic",
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

    missing: list[str] = []
    for pkg in REQUIRED:
        if importlib.util.find_spec(pkg) is None:
            missing.append(pkg)
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
                if missing:
                    print("ERROR: The following packages are still missing after the installation attempt:", ", ".join(missing))
                    return 1
        else:
            hint = "pip install " + " ".join(missing)
            if wheelhouse:
                hint = f"pip install --no-index --find-links {wheelhouse} " + " ".join(missing)
            print("Some features may be degraded. Install with:", hint)

    if not missing:
        print("Environment OK")
    return 0

if __name__ == '__main__':
    sys.exit(main())
