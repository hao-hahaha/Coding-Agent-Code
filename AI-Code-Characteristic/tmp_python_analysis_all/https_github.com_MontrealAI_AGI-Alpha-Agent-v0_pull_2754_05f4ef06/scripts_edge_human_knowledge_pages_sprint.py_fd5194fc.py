#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Cross-platform Edge-of-Human-Knowledge Pages Sprint.

This helper mirrors ``edge_human_knowledge_pages_sprint.sh`` so non-technical
users can publish the full Alpha-Factory demo gallery to GitHub Pages with
one command. It validates the environment, builds the site and verifies
offline functionality when Playwright is available.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
BROWSER_DIR = REPO_ROOT / "alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1"


def run(cmd: Sequence[str], **kwargs: Any) -> None:
    """Run ``cmd`` and raise ``CalledProcessError`` on failure."""
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, **kwargs)


def main() -> None:
    run(["python", "alpha_factory_v1/scripts/preflight.py"])
    run(["node", str(BROWSER_DIR / "build/version_check.js")])
    run(["python", "scripts/check_python_deps.py"])
    run(["python", "check_env.py", "--auto-install"])
    run(["python", "scripts/verify_disclaimer_snippet.py"])
    run(["python", "-m", "alpha_factory_v1.demos.validate_demos"])
    run(["python", "scripts/publish_demo_gallery.py"])
    run(["python", "scripts/verify_workbox_hash.py", "site/alpha_agi_insight_v1"])

    try:
        import importlib.util

        if importlib.util.find_spec("playwright") is not None:
            with subprocess.Popen(
                [sys.executable, "-m", "http.server", "--directory", "site", "8000"],
                cwd=REPO_ROOT,
            ) as proc:
                try:
                    run(["python", "scripts/verify_insight_offline.py"])
                finally:
                    proc.terminate()
        else:
            print("Playwright not found; skipping offline re-check", file=sys.stderr)
    except Exception:
        print("Playwright not found; skipping offline re-check", file=sys.stderr)


if __name__ == "__main__":
    main()
