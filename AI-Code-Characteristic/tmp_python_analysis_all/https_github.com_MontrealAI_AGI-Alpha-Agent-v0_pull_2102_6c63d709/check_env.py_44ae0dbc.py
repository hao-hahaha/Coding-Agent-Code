# SPDX-License-Identifier: Apache-2.0
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
run so the demos remain usable in restricted setups. Missing ``numpy`` or
``pandas`` normally aborts execution with an error unless the
``--allow-basic-fallback`` flag is supplied. It also performs a
quick DNS lookup to detect whether the host has network access. When
``--auto-install`` is used without connectivity and no ``--wheelhouse``
is provided the script exits early with instructions rather than waiting
for ``pip`` timeouts.

Use ``--demo <name>`` to validate extra packages required by a specific
demo. Currently ``macro_sentinel`` checks for ``gradio``, ``aiohttp`` and
``qdrant-client``.
"""

import importlib.util
import subprocess
import os
import sys
import argparse
import socket
from pathlib import Path
from typing import List, Optional


def check_pkg(pkg: str) -> bool:
    """Return ``True`` if *pkg* is importable."""
    try:
        return importlib.util.find_spec(pkg) is not None
    except Exception:  # pragma: no cover - importlib failure is unexpected
        return False

CORE = ["numpy", "yaml", "pandas"]


def warn_missing_core() -> List[str]:
    """Return any missing foundational packages and print a warning."""
    missing = [pkg for pkg in CORE if importlib.util.find_spec(pkg) is None]
    if missing:
        print("WARNING: Missing core packages:", ", ".join(missing))
    return missing


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

# Additional requirements for specific demos
DEMO_PACKAGES = {
    "macro_sentinel": [
        "gradio",
        "aiohttp",
        "qdrant_client",
    ],
}

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
    "gradio": "gradio",
    "aiohttp": "aiohttp",
    "opentelemetry": "opentelemetry-api",
    "opentelemetry-api": "opentelemetry-api",
    "qdrant_client": "qdrant-client",
}

IMPORT_NAMES = {
    "opentelemetry-api": "opentelemetry",
}


def has_network() -> bool:
    """Return ``True`` if DNS resolution for ``pypi.org`` succeeds."""
    try:
        socket.gethostbyname("pypi.org")
        return True
    except OSError:
        return False


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate runtime dependencies",
        epilog="Example: pip wheel -r requirements.txt -w /media/wheels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Attempt pip install of any missing packages",
    )
    parser.add_argument(
        "--wheelhouse",
        help="Optional path to a local wheelhouse for offline installs",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("PIP_TIMEOUT", "600")),
        help="Seconds before pip install operations abort (default: 600)",
    )
    parser.add_argument(
        "--allow-basic-fallback",
        action="store_true",
        help="Continue even if numpy or pandas are missing",
    )
    parser.add_argument(
        "--demo",
        help="Validate additional packages for the specified demo",
    )

    args = parser.parse_args(argv)

    wheelhouse = args.wheelhouse or os.getenv("WHEELHOUSE")
    auto = args.auto_install or os.getenv("AUTO_INSTALL_MISSING") == "1"
    pip_timeout = args.timeout
    allow_basic = args.allow_basic_fallback
    demo = args.demo
    extra_required = DEMO_PACKAGES.get(demo, [])

    if auto and not wheelhouse and not has_network():
        print(
            "Network unavailable. Build a wheelhouse as shown in AGENTS.md "
            "and re-run with '--wheelhouse <dir>' (see "
            "alpha_factory_v1/scripts/README.md)."
        )
        return 1

    if auto:
        for pkg in ("numpy", "prometheus_client"):
            if not check_pkg(pkg):
                cmd = [sys.executable, "-m", "pip", "install", "--quiet"]
                if wheelhouse:
                    cmd += ["--no-index", "--find-links", wheelhouse]
                cmd += [PIP_NAMES.get(pkg, pkg)]
                print(
                    f"Ensuring {pkg} (timeout {pip_timeout}s):",
                    " ".join(cmd),
                    flush=True,
                )
                try:
                    subprocess.run(cmd, check=True, timeout=pip_timeout)
                except subprocess.SubprocessError as exc:
                    print(f"Failed to install {pkg}", getattr(exc, "returncode", ""))
                    return 1

    missing_core = warn_missing_core()

    if auto and missing_core:
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"]
        if wheelhouse:
            cmd += ["--no-index", "--find-links", wheelhouse]
        cmd += [PIP_NAMES.get(pkg, pkg) for pkg in missing_core]
        print(
            f"Attempting install of core packages (timeout {pip_timeout}s):",
            " ".join(cmd),
            flush=True,
        )
        try:
            subprocess.run(cmd, check=True, timeout=pip_timeout)
        except subprocess.SubprocessError as exc:
            print("Failed to install core packages", getattr(exc, "returncode", ""))
            return 1
        missing_core = warn_missing_core()

    if missing_core and not allow_basic:
        print(
            "ERROR: numpy and pandas are required for realistic results. "
            "Re-run with --allow-basic-fallback to bypass this check."
        )
        return 1
    req_file = Path(__file__).resolve().parent / "alpha_factory_v1" / "requirements.txt"
    if auto and req_file.exists():
        cmd = [sys.executable, "-m", "pip", "install", "--quiet"]
        if wheelhouse:
            cmd += ["--no-index", "--find-links", wheelhouse]
        cmd += ["-r", str(req_file)]
        print(
            f"Ensuring baseline requirements (timeout {pip_timeout}s):",
            " ".join(cmd),
            flush=True,
        )
        try:
            subprocess.run(cmd, check=True, timeout=pip_timeout)
        except subprocess.TimeoutExpired:
            print(
                "Timed out installing baseline requirements. "
                "Build a wheelhouse as shown in AGENTS.md and re-run with "
                "'--wheelhouse <dir>' (see alpha_factory_v1/scripts/README.md).",
            )
            if not has_network() and not wheelhouse:
                print("No network connectivity detected.")
            return 1
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr or ""
            print("Failed to install baseline requirements", exc.returncode)
            if any(kw in stderr.lower() for kw in ["connection", "temporary failure", "network", "resolve"]):
                print(
                    "Network failure detected. Build a wheelhouse as shown in "
                    "AGENTS.md and re-run with '--wheelhouse <dir>' (see "
                    "alpha_factory_v1/scripts/README.md)."
                )
            return exc.returncode

    missing_required: list[str] = []
    missing_optional: list[str] = []
    for pkg in REQUIRED + extra_required + OPTIONAL:
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
            print(
                f"Attempting automatic install (timeout {pip_timeout}s):",
                " ".join(cmd),
                flush=True,
            )
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=pip_timeout,
                )
            except subprocess.TimeoutExpired:
                print(
                    "Timed out installing packages. Build a wheelhouse as shown in AGENTS.md and re-run with "
                    "'--wheelhouse <dir>' (see alpha_factory_v1/scripts/README.md)."
                )
                if not has_network() and not wheelhouse:
                    print("No network connectivity detected.")
                return 1
            except subprocess.CalledProcessError as exc:
                stderr = exc.stderr or ""
                print("Automatic install failed with code", exc.returncode)
                if any(kw in stderr.lower() for kw in ["connection", "temporary failure", "network", "resolve"]):
                    print(
                        "Network failure detected. Build a wheelhouse as shown in "
                        "AGENTS.md and re-run with '--wheelhouse <dir>' (see "
                        "alpha_factory_v1/scripts/README.md)."
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
