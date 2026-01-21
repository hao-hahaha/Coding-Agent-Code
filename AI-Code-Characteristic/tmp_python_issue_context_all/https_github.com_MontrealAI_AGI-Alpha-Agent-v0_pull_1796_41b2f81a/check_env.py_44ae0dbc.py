"""Light-weight dependency check for demos and tests.

This helper validates that the Python packages required by the
Alpha‑Factory demos and unit tests are present.  When invoked with the
``--auto-install`` flag (or ``AUTO_INSTALL_MISSING=1`` environment
variable) it ensures ``alpha_factory_v1/requirements.txt`` is installed
before attempting to resolve any remaining missing packages with
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
from pathlib import Path
from typing import List, Optional

CORE = ["numpy", "yaml", "pandas"]


def warn_missing_core() -> None:
    missing = [pkg for pkg in CORE if importlib.util.find_spec(pkg) is None]
    if missing:
        print("WARNING: Missing core packages:", ", ".join(missing))


REQUIRED = [
    "pytest",
    "prometheus_client",
    "openai",
    "anthropic",
    "fastapi",
    "opentelemetry",
    "opentelemetry-api",
    "uvicorn",
    "httpx",
    "grpc",
    "cryptography",
    "numpy",
    "google.protobuf",
    "cachetools",
    "yaml",
    "click",
    "requests",
    "pandas",
    "playwright.sync_api",
    "websockets",
    "pytest_benchmark",
    "hypothesis",
    "plotly",
]

# Optional integrations that may not be present in restricted environments.
OPTIONAL = [
    "openai_agents",
    "google_adk",
]

PIP_NAMES = {
    "openai_agents": "openai-agents",
    "google_adk": "google-adk",
    "grpc": "grpcio",
    "pytest_benchmark": "pytest-benchmark",
    "playwright.sync_api": "playwright",
    "websockets": "websockets",
    "google.protobuf": "protobuf",
    "cachetools": "cachetools",
    "yaml": "PyYAML",
    "opentelemetry": "opentelemetry-api",
    "opentelemetry-api": "opentelemetry-api",
}

IMPORT_NAMES = {
    "opentelemetry-api": "opentelemetry",
}


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

    warn_missing_core()

    wheelhouse = args.wheelhouse or os.getenv("WHEELHOUSE")
    auto = args.auto_install or os.getenv("AUTO_INSTALL_MISSING") == "1"
    req_file = Path(__file__).resolve().parent / "alpha_factory_v1" / "requirements.txt"
    if auto and req_file.exists():
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"]
        if wheelhouse:
            cmd += ["--no-index", "--find-links", wheelhouse]
        cmd += ["-r", str(req_file)]
        print("Ensuring baseline requirements:", " ".join(cmd))
        try:
            subprocess.run(cmd, check=True, timeout=600)
        except subprocess.TimeoutExpired:
            print(
                "Timed out installing baseline requirements. "
                "Re-run with '--wheelhouse <path>' to install offline packages."
            )
            return 1
        except subprocess.CalledProcessError as exc:
            print("Failed to install baseline requirements", exc.returncode)
            return exc.returncode

    missing_required: list[str] = []
    missing_optional: list[str] = []
    for pkg in REQUIRED + OPTIONAL:
        import_name = IMPORT_NAMES.get(pkg, pkg)
        try:
            spec = importlib.util.find_spec(import_name)
        except (ValueError, ModuleNotFoundError):
            # handle cases where a namespace package left an invalid entry
            # or the root package itself is missing
            spec = None
        if spec is None:
            if pkg in OPTIONAL:
                missing_optional.append(pkg)
            else:
                missing_required.append(pkg)
    missing = missing_required + missing_optional
    if missing:
        print("WARNING: Missing packages:", ", ".join(missing))
        if auto:
            cmd = [sys.executable, "-m", "pip", "install", "--quiet"]
            if wheelhouse:
                cmd += ["--no-index", "--find-links", wheelhouse]
            packages = [PIP_NAMES.get(pkg, pkg) for pkg in missing]
            cmd += packages
            print("Attempting automatic install:", " ".join(cmd))
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=600)
            except subprocess.TimeoutExpired:
                print(
                    "Timed out installing packages. Re-run with '--wheelhouse <path>' " "to install from local wheels."
                )
                return 1
            except subprocess.CalledProcessError as exc:
                stderr = exc.stderr or ""
                print("Automatic install failed with code", exc.returncode)
                if any(kw in stderr.lower() for kw in ["connection", "temporary failure", "network", "resolve"]):
                    print(
                        "Network failure detected. Re-run with '--wheelhouse <path>' "
                        "or set WHEELHOUSE to install offline packages."
                    )
                return 1
            else:
                if result.returncode != 0:
                    print("Automatic install failed with code", result.returncode)
                    return result.returncode
                print("Install completed, verifying …")
                missing = [p for p in missing if importlib.util.find_spec(IMPORT_NAMES.get(p, p)) is None]
                missing_required = [p for p in missing if p not in OPTIONAL]
                if missing_required:
                    print(
                        "ERROR: The following packages are still missing after the installation attempt:",
                        ", ".join(missing_required),
                    )
                    return 1
        else:
            hint = "pip install " + " ".join(missing)
            if wheelhouse:
                hint = f"pip install --no-index --find-links {wheelhouse} " + " ".join(missing)
            print("Some features may be degraded. Install with:", hint)

    if not missing_required:
        print("Environment OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
