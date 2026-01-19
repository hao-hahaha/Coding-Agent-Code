#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Open a specific demo from the subdirectory gallery."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from alpha_factory_v1.utils.disclaimer import DISCLAIMER
except Exception:  # pragma: no cover - fallback when package not installed
    _DOCS_PATH = Path(__file__).resolve().parents[1] / "docs" / "DISCLAIMER_SNIPPET.md"
    DISCLAIMER = _DOCS_PATH.read_text(encoding="utf-8").strip()


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
    env = os.environ.get("AF_GALLERY_URL")
    if env:
        return f"{env.rstrip('/')}/alpha_factory_v1/demos/{demo}/index.html"
    remote = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
    repo_path = remote.split("github.com")[-1].lstrip(":/").removesuffix(".git")
    org, repo = repo_path.split("/", 1)
    return f"https://{org}.github.io/{repo}/alpha_factory_v1/demos/{demo}/index.html"


def _remote_available(url: str) -> bool:
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=3) as resp:
            status = getattr(resp, "status", None)
        return bool(status and 200 <= int(status) < 300)
    except Exception:
        return False


def main(demo: str, *, print_only: bool = False) -> None:
    print(DISCLAIMER, file=sys.stderr)
    url = _demo_url(demo)
    if _remote_available(url):
        if print_only:
            print(url)
            return
        print(f"Opening {url}")
        webbrowser.open(url)
        return

    repo_root = Path(__file__).resolve().parents[1]
    site_dir = repo_root / "site" / "alpha_factory_v1" / "demos" / demo
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
            if print_only:
                print(local_url)
            else:
                webbrowser.open(local_url)
            thread.join()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open a specific demo from the subdirectory gallery")
    parser.add_argument("demo", help="Demo name to open")
    parser.add_argument("--print-url", action="store_true", help="Only print the resolved URL")
    args = parser.parse_args()
    main(args.demo, print_only=args.print_url)
