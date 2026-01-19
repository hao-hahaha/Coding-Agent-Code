# SPDX-License-Identifier: Apache-2.0
import os
import re
import hashlib
import base64
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse
import ast


def _require_node_20() -> None:
    try:
        out = subprocess.check_output(
            ["node", "-e", "console.log(process.versions.node)"],
            text=True,
        ).strip()
    except FileNotFoundError:
        sys.exit("Node.js 20+ is required. 'node' not found.")
    major = int(out.split(".")[0])
    if major < 20:
        sys.exit(f"Node.js 20+ is required. Current version: {out}")


_require_node_20()


def sha384(path: Path) -> str:
    digest = hashlib.sha384(path.read_bytes()).digest()
    return "sha384-" + base64.b64encode(digest).decode()


ROOT = Path(__file__).resolve().parent
ALIAS_PREFIX = "@insight-src/"
repo_root = Path(__file__).resolve()
for _ in range(4):
    repo_root = repo_root.parent
ALIAS_TARGET = repo_root / "src"
index_html = ROOT / "index.html"
dist_dir = ROOT / "dist"
lib_dir = ROOT / "lib"

bundle_path = lib_dir / "bundle.esm.min.js"
try:
    data = bundle_path.read_text()
except FileNotFoundError:
    sys.exit(
        "lib/bundle.esm.min.js missing. Run scripts/fetch_assets.py to download assets."
    )
if "Placeholder for web3.storage bundle.esm.min.js" in data:
    sys.exit(
        "lib/bundle.esm.min.js is a placeholder. Run scripts/fetch_assets.py to download assets."
    )

def _asset_paths() -> list[str]:
    fetch = repo_root / 'scripts' / 'fetch_assets.py'
    tree = ast.parse(fetch.read_text())
    assets = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if getattr(t, 'id', None) == 'ASSETS':
                    assets = ast.literal_eval(node.value)
                    break
    return list(assets)


def _expected_checksums() -> dict[str, str]:
    fetch = repo_root / 'scripts' / 'fetch_assets.py'
    tree = ast.parse(fetch.read_text())
    checks: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if getattr(t, 'id', None) == 'CHECKSUMS':
                    checks = ast.literal_eval(node.value)
                    break
    return checks

for rel in _asset_paths():
    p = ROOT / rel
    if p.exists() and 'placeholder' in p.read_text(errors='ignore').lower():
        sys.exit(f"{rel} contains placeholder text. Run scripts/fetch_assets.py to download assets.")

subprocess.run(["tsc", "--noEmit"], check=True)

html = index_html.read_text()
entry = (ROOT / "app.js").read_text()


def find_deps(code):
    deps = []
    for imp in re.findall(r"import[^'\"]*['\"](.*?)['\"]", code):
        if imp.startswith(ALIAS_PREFIX) or imp.startswith("."):
            deps.append(imp)
    return deps


processed = {}
order = []


def process_module(path):
    path = Path(path)
    if path in processed:
        return
    code = path.read_text()
    for dep in find_deps(code):
        if dep.startswith(ALIAS_PREFIX):
            dep_path = (ALIAS_TARGET / dep[len(ALIAS_PREFIX):]).resolve()
        else:
            dep_path = (path.parent / dep).resolve()
            if not dep_path.exists():
                dep_path = (ROOT / dep.lstrip("./")).resolve()
        if dep_path.exists():
            process_module(dep_path)
    # strip import lines
    code = re.sub(r"^\s*import[^\n]*\n", "", code, flags=re.MULTILINE)
    # strip export keywords
    code = re.sub(r"^\s*export\s+", "", code, flags=re.MULTILINE)
    processed[path] = code
    order.append(path)


for dep in find_deps(entry):
    if dep.startswith(ALIAS_PREFIX):
        dep_path = (ALIAS_TARGET / dep[len(ALIAS_PREFIX):]).resolve()
    else:
        dep_path = (ROOT / dep).resolve()
    process_module(dep_path)

# process lib/bundle.esm.min.js if referenced
if (lib_dir / "bundle.esm.min.js").exists():
    lib_code = (lib_dir / "bundle.esm.min.js").read_text()
    lib_code = re.sub(r"^\s*export\s+", "", lib_code, flags=re.MULTILINE)
    processed[lib_dir / "bundle.esm.min.js"] = lib_code
    order.insert(0, lib_dir / "bundle.esm.min.js")

entry_code = re.sub(r"^\s*import[^\n]*\n", "", entry, flags=re.MULTILINE)

bundle = "(function() {\n" + "\n".join(processed[p] for p in order) + "\n" + entry_code + "\n})();\n"

dist_dir.mkdir(exist_ok=True)
(dist_dir / "app.js").write_text(bundle)

app_sri_placeholder = '<script type="module" src="app.js" crossorigin="anonymous"></script>'
out_html = html.replace("src/ui/controls.css", "controls.css")
ipfs_origin = os.getenv("IPFS_GATEWAY")
if ipfs_origin:
    p = urlparse(ipfs_origin)
    ipfs_origin = f"{p.scheme}://{p.netloc}"
otel_origin = os.getenv("OTEL_ENDPOINT")
if otel_origin:
    p = urlparse(otel_origin)
    otel_origin = f"{p.scheme}://{p.netloc}"
csp = "default-src 'self'; connect-src 'self' https://api.openai.com"
if ipfs_origin:
    csp += f" {ipfs_origin}"
if otel_origin:
    csp += f" {otel_origin}"
csp += "; script-src 'self' 'wasm-unsafe-eval'"
out_html = re.sub(
    r'<meta[^>]*http-equiv="Content-Security-Policy"[^>]*>',
    f'<meta http-equiv="Content-Security-Policy" content="{csp}" />',
    out_html,
)

# copy assets
for src, dest in [
    ("style.css", "style.css"),
    ("src/ui/controls.css", "controls.css"),
    ("d3.v7.min.js", "d3.v7.min.js"),
    ("lib/bundle.esm.min.js", "bundle.esm.min.js"),
    ("lib/pyodide.js", "pyodide.js"),
    ("worker/evolver.js", "worker/evolver.js"),
    ("worker/arenaWorker.js", "worker/arenaWorker.js"),
    ("src/utils/rng.js", "src/utils/rng.js"),
    ("sw.js", "sw.js"),
    ("manifest.json", "manifest.json"),
    ("favicon.svg", "favicon.svg"),
]:
    src_path = ROOT / src if isinstance(src, str) else src
    if src_path.exists():
        target = dist_dir / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(src_path.read_bytes())

# copy critic examples
critics_src = ROOT.parents[3] / "data" / "critics"
critics_dst = dist_dir / "data" / "critics"
if critics_src.exists():
    critics_dst.mkdir(parents=True, exist_ok=True)
    for f in critics_src.iterdir():
        (critics_dst / f.name).write_bytes(f.read_bytes())

app_sri = sha384(dist_dir / "app.js")
style_sri = sha384(dist_dir / "style.css")
bundle_sri = sha384(dist_dir / "bundle.esm.min.js")
pyodide_sri = sha384(dist_dir / "pyodide.js")
checksums = _expected_checksums()
out_html = out_html.replace(
    app_sri_placeholder, f'<script type="module" src="app.js" integrity="{app_sri}" crossorigin="anonymous"></script>'
)
out_html = out_html.replace(
    'href="style.css"',
    f'href="style.css" integrity="{style_sri}" crossorigin="anonymous"',
)
env_script = (
    "<script>"
    f'window.PINNER_TOKEN={json.dumps(os.getenv("PINNER_TOKEN", ""))};'
    f'window.OPENAI_API_KEY={json.dumps(os.getenv("OPENAI_API_KEY", ""))};'
    f'window.OTEL_ENDPOINT={json.dumps(os.getenv("OTEL_ENDPOINT", ""))};'
    f'window.IPFS_GATEWAY={json.dumps(os.getenv("IPFS_GATEWAY", ""))};'
    "</script>"
)
out_html = out_html.replace(
    "</body>",
    f'<script src="bundle.esm.min.js" integrity="{bundle_sri}" crossorigin="anonymous"></script>\n'
    f'<script src="pyodide.js" integrity="{pyodide_sri}" crossorigin="anonymous"></script>\n'
    f"{env_script}\n</body>",
)

if (ROOT / "wasm").exists():
    (dist_dir / "wasm").mkdir(exist_ok=True)
    for f in (ROOT / "wasm").iterdir():
        (dist_dir / "wasm" / f.name).write_bytes(f.read_bytes())
    wasm_sri = sha384(dist_dir / "wasm" / "pyodide.asm.wasm")
    expected = checksums.get("pyodide.asm.wasm")
    if expected and expected != wasm_sri:
        sys.exit("Checksum mismatch for pyodide.asm.wasm")
    out_html = out_html.replace(
        "</head>",
        f'<link rel="preload" href="wasm/pyodide.asm.wasm" as="fetch" type="application/wasm" integrity="{wasm_sri}" crossorigin="anonymous" />\n</head>',
    )
else:
    wasm_sri = None
(dist_dir / "index.html").write_text(out_html)

if (ROOT / "wasm_llm").exists():
    (dist_dir / "wasm_llm").mkdir(exist_ok=True)
    for f in (ROOT / "wasm_llm").iterdir():
        (dist_dir / "wasm_llm" / f.name).write_bytes(f.read_bytes())

# generate service worker
sw_src = ROOT / "sw.js"
sw_dest = dist_dir / "sw.js"
node_script = f"""
const {{injectManifest}} = require('workbox-build');
injectManifest({{
  swSrc: {json.dumps(str(sw_src))},
  swDest: {json.dumps(str(sw_dest))},
  globDirectory: {json.dumps(str(dist_dir))},
  globPatterns: [
    'index.html',
    'app.js',
    'style.css',
    'd3.v7.min.js',
    'pyodide.*',
    'wasm_llm/*',
    'wasm/*',
    'worker/*',
    'data/critics/*',
  ],
}}).catch(err => {{console.error(err); process.exit(1);}});
"""
try:
    subprocess.run(["node", "-e", node_script], check=True)
except FileNotFoundError:
    print("[manual_build] node not found; skipping service worker generation", file=sys.stderr)
except subprocess.CalledProcessError as exc:
    print(f"[manual_build] workbox build failed: {exc}; offline features disabled", file=sys.stderr)
