#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Open a specific Alpha-Factory demo in a web browser.

This utility mirrors ``open_demo.sh`` but is cross-platform. It first attempts
to open the published GitHub Pages URL for the requested demo. If the remote
page is unavailable, a local copy under ``./site/<demo>`` is served instead.
When the local files are missing, the gallery is built automatically so
non-technical users can explore the demos with a single command.
"""
from __future__ import annotations

import subprocess
import sys
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen


def _build_local_site(repo_root: Path) -> bool:
    script = repo_root / "scripts" / "build_gallery_site.sh"
    if not script.is_file():
        return False
    try:
        subprocess.run([str(script)], check=True)
    except Exception:
        return False
    return True


def _demo_url(demo: str) -> str:
    remote = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
    repo_path = remote.split("github.com")[-1].lstrip(":/")
    repo_path = repo_path.removesuffix(".git")
    org, repo = repo_path.split("/", 1)
    return f"https://{org}.github.io/{repo}/{demo}/"


def _remote_available(url: str) -> bool:
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=3) as resp:
            status = getattr(resp, "status", None)
        return bool(status and 200 <= int(status) < 300)
    except Exception:
        return False


def main(demo: str) -> None:
    url = _demo_url(demo)
    if _remote_available(url):
        print(f"Opening {url}")
        webbrowser.open(url)
        return

    repo_root = Path(__file__).resolve().parents[1]
    site_dir = repo_root / "site" / demo
    local_page = site_dir / "index.html"
    if not local_page.is_file():
        print("Remote page unavailable. Building local copy...", file=sys.stderr)
        if not _build_local_site(repo_root) or not local_page.is_file():
            print(
                f"Demo {demo} not found. Build the gallery with ./scripts/build_gallery_site.sh",
                file=sys.stderr,
            )
            sys.exit(1)

    handler = partial(SimpleHTTPRequestHandler, directory=str(site_dir))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        local_url = f"http://127.0.0.1:{port}/index.html"
        print(f"Serving local copy at {local_url}", file=sys.stderr)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            webbrowser.open(local_url)
            thread.join()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: open_demo.py <demo_name>", file=sys.stderr)
        raise SystemExit(1)
    main(sys.argv[1])
