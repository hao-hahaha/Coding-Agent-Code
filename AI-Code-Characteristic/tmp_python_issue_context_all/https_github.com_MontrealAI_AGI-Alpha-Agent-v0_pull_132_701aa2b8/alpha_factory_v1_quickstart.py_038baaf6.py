#!/usr/bin/env python3
"""Cross-platform Quickstart launcher for Alpha-Factory v1.

This utility mirrors ``quickstart.sh`` but works on Windows and other
systems lacking Bash. It bootstraps a virtual environment, installs
required packages and optionally runs preflight checks before starting
the orchestrator.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _venv_python(venv: Path) -> Path:
    """Return the path to the Python interpreter inside *venv*."""
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def _venv_pip(venv: Path) -> Path:
    """Return the path to the pip executable inside *venv*."""
    if os.name == "nt":
        return venv / "Scripts" / "pip.exe"
    return venv / "bin" / "pip"


def _create_venv(venv: Path) -> None:
    """Create *venv* and install dependencies if missing."""
    if not venv.exists():
        print("\u2192 Creating virtual environment")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
        pip = _venv_pip(venv)
        subprocess.check_call([str(pip), "install", "-U", "pip"], stdout=subprocess.DEVNULL)
        req = Path("alpha_factory_v1/requirements.lock")
        if not req.exists():
            req = Path("alpha_factory_v1/requirements.txt")
        subprocess.check_call([str(pip), "install", "-r", str(req)])


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Alpha-Factory Quickstart")
    parser.add_argument("--preflight", action="store_true", help="Run checks and exit")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip checks")
    parser.add_argument("orchestrator_args", nargs=argparse.REMAINDER, help="Arguments passed to orchestrator")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent
    os.chdir(repo_root)
    venv = repo_root / ".venv"
    _create_venv(venv)

    py = _venv_python(venv)

    if args.preflight:
        subprocess.check_call([str(py), "alpha_factory_v1/scripts/preflight.py"])
        return

    if not args.skip_preflight:
        subprocess.check_call([str(py), "alpha_factory_v1/scripts/preflight.py"])

    cmd = [str(py), "-m", "alpha_factory_v1.run"] + args.orchestrator_args
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
