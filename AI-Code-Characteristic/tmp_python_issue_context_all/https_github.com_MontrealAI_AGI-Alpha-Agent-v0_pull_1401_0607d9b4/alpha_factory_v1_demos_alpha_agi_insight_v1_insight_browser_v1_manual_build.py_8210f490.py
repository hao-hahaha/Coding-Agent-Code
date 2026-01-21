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


def sha384(path: Path) -> str:
    digest = hashlib.sha384(path.read_bytes()).digest()
    return "sha384-" + base64.b64encode(digest).decode()


ROOT = Path(__file__).resolve().parent
index_html = ROOT / "index.html"
dist_dir = ROOT / "dist"
lib_dir = ROOT / "lib"
src_dir = ROOT / "src"

html = index_html.read_text()
entry = (ROOT / "app.js").read_text()


def find_deps(code):
    deps = []
    for imp in re.findall(r"import[^'\"]*['\"](.*?)['\"]", code):
        if imp.startswith("."):  # relative
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
(dist_dir / "index.html").write_text(out_html)

if (ROOT / "wasm").exists():
    (dist_dir / "wasm").mkdir(exist_ok=True)
    for f in (ROOT / "wasm").iterdir():
        (dist_dir / "wasm" / f.name).write_bytes(f.read_bytes())

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
