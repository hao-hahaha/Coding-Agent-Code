#!/usr/bin/env python3
"""One-click launcher for the Alpha‑AGI Business v1 demo.

This helper checks dependencies, starts the local orchestrator with the
OpenAI Agents bridge enabled, and opens the REST dashboard in the
system default web browser.  Useful for non‑technical users.
"""
import os
import subprocess
import sys
import time
import webbrowser

import check_env


SCRIPT_DIR = os.path.dirname(__file__)


def main() -> None:
    try:
        check_env.main(["--auto-install"])
    except Exception as exc:  # pragma: no cover - optional network failure
        print(f"⚠️  Environment check failed: {exc}")

    env = os.environ.copy()
    port = env.get("PORT", "8000")
    cmd = [sys.executable, "run_business_v1_local.py", "--bridge"]
    proc = subprocess.Popen(cmd, cwd=SCRIPT_DIR, env=env)

    url = f"http://localhost:{port}/docs"
    for _ in range(MAX_HEALTH_CHECK_RETRIES):
        if proc.poll() is not None:
            break
        try:

            if requests.get(f"http://localhost:{port}/healthz", timeout=1).status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    try:
        webbrowser.open(url, new=1)
    except Exception:
        print(f"Open {url} to access the dashboard")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
