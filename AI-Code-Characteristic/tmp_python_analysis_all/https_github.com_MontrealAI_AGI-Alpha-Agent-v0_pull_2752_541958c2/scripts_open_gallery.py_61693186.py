#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Open the Alpha-Factory demo gallery in a web browser.

This helper mirrors ``open_gallery.sh`` but uses Python for portability.  It
attempts to open the published GitHub Pages gallery and falls back to a local
build under ``site/`` when offline.  If the local build is missing, the script
automatically runs ``scripts/build_gallery_site.sh`` to generate the site so
non‑technical users can access the demos with a single command.  When serving
the local copy, a lightweight HTTP server is spawned to preserve all
functionality such as service workers and relative assets.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading


def _build_local_site(repo_root: Path) -> bool:
    """Return ``True`` if the gallery was built successfully."""
    script = repo_root / "scripts" / "build_gallery_site.sh"
    if not script.is_file():
        return False
    try:
        subprocess.run([str(script)], check=True)
    except Exception:
        return False
    return True


def _gallery_url() -> str:
    remote = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
    repo_path = remote.split("github.com")[-1].lstrip(":/")
    repo_path = repo_path.removesuffix(".git")
    org, repo = repo_path.split("/", 1)
    return f"https://{org}.github.io/{repo}/gallery.html"


def _remote_available(url: str) -> bool:
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=3) as resp:
            status = getattr(resp, "status", None)
        return bool(status and 200 <= int(status) < 300)
    except Exception:
        return False


def main() -> None:
    url = _gallery_url()
    if _remote_available(url):
        print(f"Opening {url}")
        webbrowser.open(url)
        return
    repo_root = Path(__file__).resolve().parents[1]
    site_dir = repo_root / "site"
    local_page = site_dir / "gallery.html"
    if not local_page.is_file():
        print("Remote gallery unavailable. Building local copy...", file=sys.stderr)
        if not _build_local_site(repo_root) or not local_page.is_file():
            print(
                "Gallery not found. Build it with ./scripts/build_gallery_site.sh",
                file=sys.stderr,
            )
            sys.exit(1)

    handler = partial(SimpleHTTPRequestHandler, directory=str(site_dir))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        url = f"http://127.0.0.1:{port}/gallery.html"
        print(f"Remote gallery unavailable. Serving local copy at {url}", file=sys.stderr)

        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            webbrowser.open(url)
            thread.join()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
