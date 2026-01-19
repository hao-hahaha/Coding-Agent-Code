#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Open the Alpha-Factory subdirectory demo gallery in a browser.

This helper mirrors ``open_gallery.py`` but targets the mirror under
``alpha_factory_v1/demos/`` so users can explore demos from that
sub-directory of the GitHub Pages site. It gracefully falls back to a
local build when offline by invoking ``scripts/build_gallery_site.sh``.
"""
from __future__ import annotations

from alpha_factory_v1.utils.disclaimer import DISCLAIMER
import argparse

import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading


def _build_local_site(repo_root: Path) -> bool:
    script = repo_root / "scripts" / "build_gallery_site.sh"
    if not script.is_file():
        return False
    try:
        subprocess.run([str(script)], check=True)
    except Exception:
        return False
    return True


def _subdir_url() -> str:
    remote = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
    repo_path = remote.split("github.com")[-1].lstrip(":/")
    repo_path = repo_path.removesuffix(".git")
    org, repo = repo_path.split("/", 1)
    return f"https://{org}.github.io/{repo}/alpha_factory_v1/demos/"


def _remote_available(url: str) -> bool:
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=3) as resp:
            status = getattr(resp, "status", None)
        return bool(status and 200 <= int(status) < 300)
    except Exception:
        return False


def main(demo: str | None = None) -> None:
    print(DISCLAIMER, file=sys.stderr)
    base_url = _subdir_url()
    if demo:
        remote_page = f"{base_url}{demo}/index.html"
    else:
        remote_page = base_url + "index.html"
    if _remote_available(remote_page):
        print(f"Opening {remote_page}")
        webbrowser.open(remote_page)
        return
    repo_root = Path(__file__).resolve().parents[1]
    site_dir = repo_root / "site"
    local_page = site_dir / "alpha_factory_v1" / "demos"
    if demo:
        local_page = local_page / demo / "index.html"
    else:
        local_page = local_page / "index.html"
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
        path = "alpha_factory_v1/demos/"
        if demo:
            path += f"{demo}/index.html"
        else:
            path += "index.html"
        local_url = f"http://127.0.0.1:{port}/{path}"
        print(
            f"Remote gallery unavailable. Serving local copy at {local_url}",
            file=sys.stderr,
        )

        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            webbrowser.open(local_url)
            thread.join()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open the demo gallery")
    parser.add_argument(
        "demo",
        nargs="?",
        help="Specific demo to open (default: full gallery)",
    )
    args = parser.parse_args()
    main(args.demo)
