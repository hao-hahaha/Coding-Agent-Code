"""Run environment checks before installing Alpha-Factory.

The script verifies Python compatibility, essential command line tools,
Docker availability and key Python packages.  Optional demo integrations
like ``openai`` or ``google_adk`` are detected as well so users know
which extras to install for full functionality.
"""

import os
import shutil
import sys
import subprocess
import tempfile
from pathlib import Path

MIN_PY = (3, 11)
MAX_PY = (3, 13)
MEM_DIR = Path(os.getenv("AF_MEMORY_DIR", f"{tempfile.gettempdir()}/alphafactory"))

COLORS = {
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "RESET": "\033[0m",
}


def banner(msg: str, color: str = "GREEN") -> None:
    color_code = COLORS.get(color.upper(), "")
    reset = COLORS["RESET"]
    print(f"{color_code}{msg}{reset}")


def check_python() -> bool:
    if sys.version_info < MIN_PY or sys.version_info >= MAX_PY:
        banner(
            f"Python {MIN_PY[0]}.{MIN_PY[1]}+ and <{MAX_PY[0]}.{MAX_PY[1]} required",
            "RED",
        )
        return False
    banner(f"Python {sys.version.split()[0]} detected", "GREEN")
    return True


def check_cmd(cmd: str) -> bool:
    if shutil.which(cmd):
        banner(f"{cmd} found", "GREEN")
        return True
    banner(f"{cmd} missing", "RED")
    return False


def check_docker_daemon() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        subprocess.run(["docker", "info"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        banner("docker daemon reachable", "GREEN")
        return True
    except Exception:  # noqa: BLE001
        banner("docker daemon not running", "RED")
        return False


def check_docker_compose() -> bool:
    if not shutil.which("docker"):
        banner("docker compose missing", "RED")
        return False
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        banner("docker compose available", "GREEN")
        return True
    except Exception:  # noqa: BLE001
        banner("docker compose missing", "RED")
        return False


def check_pkg(pkg: str) -> bool:
    """Return True if *pkg* is importable."""
    try:
        import importlib.util

        found = importlib.util.find_spec(pkg) is not None
    except Exception:  # pragma: no cover - importlib failure is unexpected
        found = False
    banner(f"{pkg} {'found' if found else 'missing'}", "GREEN" if found else "RED")
    return found


def ensure_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        banner(f"Created {path}", "YELLOW")
    else:
        banner(f"Using {path}", "GREEN")


OPTIONAL_DEPS = {
    "openai": [
        "alpha_agi_business_v1",
        "macro_sentinel",
        "alpha_asi_world_model",
    ],
    "openai_agents": ["alpha_asi_world_model", "macro_sentinel"],
    "anthropic": ["alpha_asi_world_model", "sovereign_agentic_agialpha_agent_v0"],
    "google_adk": ["omni_factory_demo", "meta_agentic_tree_search_v0"],
}


def main() -> None:
    banner("Alpha-Factory Preflight Check", "YELLOW")
    ok = True
    ok &= check_python()
    ok &= check_cmd("docker")
    ok &= check_cmd("git")
    ok &= check_docker_daemon()
    ok &= check_docker_compose()
    # Always install pytest and prometheus_client for smooth local tests
    ok &= check_pkg("pytest")
    ok &= check_pkg("prometheus_client")

    missing_optional: list[str] = []
    for pkg in OPTIONAL_DEPS:
        if not check_pkg(pkg):
            missing_optional.append(pkg)

    ensure_dir(MEM_DIR)

    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if os.getenv(key):
            banner(f"{key} set", "GREEN")
        else:
            banner(f"{key} not set", "YELLOW")

    if missing_optional:
        banner("Optional packages missing:", "YELLOW")
        for pkg in missing_optional:
            demos = ", ".join(OPTIONAL_DEPS[pkg])
            banner(f"  {pkg} ⇒ demos: {demos}", "YELLOW")

    if not ok:
        banner("Preflight checks failed. Please install required dependencies.", "RED")
        sys.exit(1)

    banner("Environment looks good. You can now run install_alpha_factory_pro.sh", "GREEN")


if __name__ == "__main__":
    main()
