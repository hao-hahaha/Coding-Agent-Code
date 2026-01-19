# SPDX-License-Identifier: Apache-2.0
"""Shared build helpers for the Insight browser."""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import subprocess
import sys
import re
from pathlib import Path


def sha384(path: Path) -> str:
    """Return the SHA-384 digest of ``path`` in SRI format."""
    digest = hashlib.sha384(path.read_bytes()).digest()
    return "sha384-" + base64.b64encode(digest).decode()


def check_gzip_size(path: Path, max_bytes: int = 2 * 1024 * 1024) -> None:
    """Exit if gzip-compressed ``path`` exceeds ``max_bytes``."""
    compressed = gzip.compress(path.read_bytes())
    if len(compressed) > max_bytes:
        sys.exit(f"gzip size {len(compressed)} bytes exceeds limit")


def generate_service_worker(root: Path, dist_dir: Path, manifest: dict) -> None:
    """Create ``sw.js`` using workbox and inject it into ``index.html``."""
    sw_src = root / "sw.js"
    sw_dest = dist_dir / "sw.js"
    version = json.loads((root / "package.json").read_text())["version"]
    temp_sw = dist_dir / "sw.build.js"
    temp_sw.write_text(sw_src.read_text().replace("__CACHE_VERSION__", version))
    node_script = f"""
const {{injectManifest}} = require('workbox-build');
injectManifest({{
  swSrc: {json.dumps(str(temp_sw))},
  swDest: {json.dumps(str(sw_dest))},
  globDirectory: {json.dumps(str(dist_dir))},
  importWorkboxFrom: 'disabled',
  globPatterns: {json.dumps(manifest['precache'])},
  injectionPoint: 'self.__WB_MANIFEST',
}}).catch(err => {{console.error(err); process.exit(1);}});
"""
    try:
        subprocess.run(["node", "-e", node_script], check=True)
    except FileNotFoundError:
        print(
            "[manual_build] node not found; skipping service worker generation",
            file=sys.stderr,
        )
    except subprocess.CalledProcessError as exc:
        print(
            f"[manual_build] workbox build failed: {exc}; offline features disabled",
            file=sys.stderr,
        )
    finally:
        temp_sw.unlink(missing_ok=True)
    sw_hash = sha384(sw_dest)
    index_path = dist_dir / "index.html"
    text = index_path.read_text()
    text = text.replace(".register('sw.js')", ".register('service-worker.js')")
    text = text.replace(
        "</body>",
        f'<script src="service-worker.js" integrity="{sw_hash}" crossorigin="anonymous"></script>\n</body>',
    )
    text = re.sub(r"(script-src 'self' 'wasm-unsafe-eval')", rf"\1 '{sw_hash}'", text)
    index_path.write_text(text)
