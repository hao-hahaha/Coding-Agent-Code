#!/usr/bin/env python3
"""One-click launcher for the Alpha‑AGI Business v1 demo.

This helper checks dependencies, starts the local orchestrator with the
OpenAI Agents bridge enabled, and opens the REST dashboard in the
system default web browser. Pass ``--no-browser`` to suppress the
automatic browser launch (useful in headless or Colab environments).
Use ``--submit-best`` to automatically queue the highest scoring demo
alpha opportunity once the service is ready.
"""
import argparse
import os
import subprocess
import sys
import time
import webbrowser

# allow running this script directly from its folder
SCRIPT_DIR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:  # optional dependency
    import requests  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - offline shim
    from alpha_factory_v1 import requests  # type: ignore

import check_env

# Maximum number of times to poll the orchestrator health endpoint
# before giving up on opening the dashboard.  Keep this small so the
# launcher remains responsive even when the orchestrator fails to
# start correctly.
MAX_HEALTH_CHECK_RETRIES = 20


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the alpha_agi_business_v1 demo"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open the REST docs in a web browser",
    )
    parser.add_argument(
        "--submit-best",
        action="store_true",
        help="Automatically queue the highest scoring demo opportunity",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
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
    if args.submit_best:
        runtime_port = env.get("AGENTS_RUNTIME_PORT", "5001")
        payload = {"action": "best_alpha"}
        try:
            resp = requests.post(
                f"http://localhost:{runtime_port}/v1/agents/business_helper/invoke",
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            print("Queued best alpha opportunity via BusinessAgent")
        except requests.RequestException as exc:
            print(f"⚠️  Failed to queue best alpha: {exc}")
    if not args.no_browser:
        try:
            webbrowser.open(url, new=1)
        except Exception:
            print(f"Open {url} to access the dashboard")
    else:
        print(f"Dashboard available at {url}")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
