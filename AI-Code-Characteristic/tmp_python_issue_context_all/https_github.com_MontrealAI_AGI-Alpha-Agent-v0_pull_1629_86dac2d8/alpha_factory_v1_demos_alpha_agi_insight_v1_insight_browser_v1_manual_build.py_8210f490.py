# SPDX-License-Identifier: Apache-2.0
import os
import re
import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

BUILD_DIR = Path(__file__).resolve().parent / "build"
sys.path.insert(0, str(BUILD_DIR))
from common import (  # noqa: E402
    check_gzip_size,
    sha384,
    generate_service_worker,
)


def _require_python_311() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 11):
        sys.exit(f"Python ≥3.11 required. Current version: {sys.version}")


_require_python_311()

ROOT = Path(__file__).resolve().parent
try:
    subprocess.run(
        [
            "node",
            "build/version_check.js",
        ],
        cwd=ROOT,
        check=True,
    )
except FileNotFoundError:
    sys.exit("Node.js 20+ is required. Install Node.js and ensure 'node' is in your PATH.")  # noqa: E501
except subprocess.CalledProcessError as exc:
    sys.exit(exc.returncode)

# load environment variables
env_file = Path(__file__).resolve().parent / ".env"
if not env_file.is_file():
    sys.exit(".env not found. Copy .env.sample to .env and populate the required values.")  # noqa: E501
try:
    from alpha_factory_v1.utils.env import _load_env_file

    for key, val in _load_env_file(env_file).items():
        os.environ.setdefault(key, val)
except Exception as exc:  # pragma: no cover - optional dep
    print(f"[manual_build] failed to load .env: {exc}", file=sys.stderr)


def _validate_env() -> None:
    """Validate tokens and URLs in the environment."""
    for key in ("PINNER_TOKEN", "WEB3_STORAGE_TOKEN"):
        val = os.getenv(key)
        if val is not None and not val.strip():
            sys.exit(f"{key} may not be empty")

    for key in ("IPFS_GATEWAY", "OTEL_ENDPOINT"):
        val = os.getenv(key)
        if val:
            p = urlparse(val)
            if not p.scheme or not p.netloc:
                sys.exit(f"Invalid URL in {key}")


_validate_env()


def copy_assets(
    manifest: dict[str, Any],
    repo_root: Path,
    dist_dir: Path,
) -> None:
    for rel in manifest["files"]:
        src_path = ROOT / rel
        if src_path.exists():
            target = dist_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(src_path.read_bytes())

    translations = ROOT / manifest["dirs"]["translations"]
    if translations.exists():
        for f in translations.iterdir():
            if f.is_file():
                target = dist_dir / manifest["dirs"]["translations"] / f.name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f.read_bytes())

    critics_src = repo_root / manifest["dirs"]["critics"]
    critics_dst = dist_dir / manifest["dirs"]["critics"]
    if critics_src.exists():
        critics_dst.mkdir(parents=True, exist_ok=True)
        for f in critics_src.iterdir():
            (critics_dst / f.name).write_bytes(f.read_bytes())

    for key in ("wasm", "wasm_llm"):
        d = ROOT / manifest["dirs"][key]
        if d.exists():
            target_dir = dist_dir / manifest["dirs"][key]
            target_dir.mkdir(exist_ok=True)
            for f in d.iterdir():
                (target_dir / f.name).write_bytes(f.read_bytes())


def _enc(val: str | None) -> str:
    return base64.b64encode(str(val or "").encode()).decode()


def inject_env() -> str:
    return (
        "<script>"
        f"window.PINNER_TOKEN=atob('{_enc(os.getenv('PINNER_TOKEN'))}');"
        f"window.OTEL_ENDPOINT=atob('{_enc(os.getenv('OTEL_ENDPOINT'))}');"
        f"window.IPFS_GATEWAY=atob('{_enc(os.getenv('IPFS_GATEWAY'))}');"
        "</script>"
    )


ROOT = Path(__file__).resolve().parent
ALIAS_PREFIX = "@insight-src/"
repo_root = Path(__file__).resolve()
for _ in range(5):
    repo_root = repo_root.parent
ALIAS_TARGET = repo_root / "src"
index_html = ROOT / "index.html"
dist_dir = ROOT / "dist"
lib_dir = ROOT / "lib"
manifest = json.loads((ROOT / "build_assets.json").read_text())
quickstart_pdf = repo_root / manifest["quickstart_pdf"]

bundle_path = lib_dir / "bundle.esm.min.js"
workbox_path = lib_dir / "workbox-sw.js"


def _ensure_assets() -> None:
    placeholders = []
    for p in (bundle_path, workbox_path):
        if p.exists():
            data = p.read_text(errors="ignore")
            if "placeholder" in data.lower():
                placeholders.append(p)
        else:
            placeholders.append(p)
    if placeholders:
        print("Fetching missing browser assets...")
        subprocess.run(
            [sys.executable, str(repo_root / "scripts/fetch_assets.py")],
            check=True,
        )
        for p in placeholders:
            text = p.read_text(errors="ignore").lower() if p.exists() else ""
            if not p.exists() or "placeholder" in text:
                sys.exit(f"Failed to download {p.relative_to(ROOT)}")


_ensure_assets()


def _placeholder_files() -> list[Path]:
    paths: list[Path] = []
    root = ROOT / "lib"
    if root.exists():
        for p in root.rglob("*"):
            if p.is_file():
                text = p.read_text(errors="ignore").lower()
                if "placeholder" in text:
                    paths.append(p)
    return paths


placeholders = _placeholder_files()
if placeholders:
    print("Detected placeholder assets, running fetch_assets.py...")
    subprocess.run(
        [sys.executable, str(repo_root / "scripts/fetch_assets.py")],
        check=True,
    )
    placeholders = _placeholder_files()
    if placeholders:
        sys.exit(f"Placeholder text found in {placeholders[0]}")


try:
    subprocess.run(["tsc", "--noEmit"], check=True)
except FileNotFoundError:
    sys.exit("TypeScript compiler not found – run `npm install` first.")


def _compile_worker(path: Path) -> str:
    script = (
        "const ts=require('typescript');"
        "const fs=require('fs');"
        "const src=fs.readFileSync(process.argv[1],'utf8');"
        "const out=ts.transpileModule(src,{compilerOptions:{module:'ES2022',target:'ES2022'}});"  # noqa: E501
        "process.stdout.write(out.outputText);"
    )
    return subprocess.check_output(
        ["node", "-e", script, str(path)],
        text=True,
    )  # noqa: E501


html = index_html.read_text()
entry = (ROOT / "app.js").read_text()


def find_deps(code: str) -> list[str]:
    deps = []
    for imp in re.findall(r"import[^'\"]*['\"](.*?)['\"]", code):
        if imp.startswith(ALIAS_PREFIX) or imp.startswith("."):
            deps.append(imp)
    return deps


processed = {}
order = []


def process_module(path: Path) -> None:
    if path in processed:
        return
    code = path.read_text()
    for dep in find_deps(code):
        if dep.startswith(ALIAS_PREFIX):
            dep_slice = dep[len(ALIAS_PREFIX) :]  # noqa: E203
            dep_path = (ALIAS_TARGET / dep_slice).resolve()  # noqa: E203
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
        dep_slice = dep[len(ALIAS_PREFIX) :]  # noqa: E203
        dep_path = (ALIAS_TARGET / dep_slice).resolve()  # noqa: E203
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

css = (
    (ROOT / "src" / "style" / "theme.css").read_text()
    + (ROOT / "dist" / "style.css").read_text()
    + (ROOT / "src" / "ui" / "controls.css").read_text()
)
d3_code = (ROOT / "d3.v7.min.js").read_text()
web3_code = (lib_dir / "bundle.esm.min.js").read_text()
web3_code = re.sub(r"^\s*export\s+", "", web3_code, flags=re.MULTILINE)
web3_code += "\nwindow.Web3Storage=Web3Storage;"
py_code = (lib_dir / "pyodide.js").read_text()
py_code = re.sub(r"^\s*export\s+", "", py_code, flags=re.MULTILINE)
py_code += "\nwindow.loadPyodide=loadPyodide;"
checksums = manifest["checksums"]


def _verify(path: Path, name: str) -> bytes:
    data = path.read_bytes()
    expected = checksums.get(name)
    if expected:
        actual = sha384(path)
        if expected != actual:
            sys.exit(f"Checksum mismatch for {name}")
    return data


wasm_b64 = ""
wasm_file = ROOT / "wasm" / "pyodide.asm.wasm"
if wasm_file.exists():
    wasm_b64 = base64.b64encode(_verify(wasm_file, "pyodide.asm.wasm")).decode()
for name in ("pyodide.js", "pyodide_py.tar", "packages.json"):
    f = ROOT / "wasm" / name
    if f.exists():
        _verify(f, name)
gpt2_b64 = ""
gpt2_file = ROOT / "wasm_llm" / "wasm-gpt2.tar"
if gpt2_file.exists():
    gpt2_b64 = base64.b64encode(_verify(gpt2_file, "wasm-gpt2.tar")).decode()
evolver = _compile_worker(ROOT / "worker" / "evolver.ts")
arena = _compile_worker(ROOT / "worker" / "arenaWorker.ts")
bundle = (
    d3_code
    + "\n"
    + web3_code
    + "\n"
    + py_code
    + f"\nwindow.PYODIDE_WASM_BASE64='{wasm_b64}';window.GPT2_MODEL_BASE64='{gpt2_b64}';\n"  # noqa: E501
    + "(function() {\nconst style="
    + repr(css)
    + ";\nconst s=document.createElement('style');s.textContent=style;document.head.appendChild(s);\nconst EVOLVER_URL=URL.createObjectURL(new Blob(["  # noqa: E501
    + repr(evolver)
    + "],{type:'text/javascript'}));\nconst ARENA_URL=URL.createObjectURL(new Blob(["  # noqa: E501
    + repr(arena)
    + "],{type:'text/javascript'}));\n"
    + "\n".join(processed[p] for p in order)
    + "\n"
    + entry_code
    + "\n})();\n"
)
bundle = re.sub(
    r"^//#\\s*sourceMappingURL=.*(?:\r?\n)?",
    "",
    bundle,
    flags=re.MULTILINE,
)

dist_dir.mkdir(exist_ok=True)
(dist_dir / "insight.bundle.js").write_text(bundle)
check_gzip_size(dist_dir / "insight.bundle.js")

app_sri_placeholder = '<script type="module" src="insight.bundle.js" crossorigin="anonymous"></script>'  # noqa: E501
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

copy_assets(manifest, repo_root, dist_dir)
if quickstart_pdf.exists():
    (dist_dir / quickstart_pdf.name).write_bytes(quickstart_pdf.read_bytes())

app_sri = sha384(dist_dir / "insight.bundle.js")
checksums = manifest["checksums"]
out_html = out_html.replace(
    app_sri_placeholder,
    (
        '<script type="module" src="insight.bundle.js" '
        + f'integrity="{app_sri}" '
        + 'crossorigin="anonymous"></script>'
    ),
)
env_script = inject_env()
out_html = re.sub(
    r"<script[\s\S]*?d3\.v7\.min\.js[\s\S]*?</script>\s*",
    "",
    out_html,
)
out_html = re.sub(
    r"<script[\s\S]*?bundle\.esm\.min\.js[\s\S]*?</script>\s*",
    "",
    out_html,
)
out_html = re.sub(
    r"<script[\s\S]*?pyodide\.js[\s\S]*?</script>\s*",
    "",
    out_html,
)
out_html = out_html.replace(
    "</body>",
    f"{env_script}\n</body>",
)

wasm_dir = ROOT / manifest["dirs"]["wasm"]
if wasm_dir.exists():
    wasm_sri = sha384(dist_dir / manifest["dirs"]["wasm"] / "pyodide.asm.wasm")
    expected = checksums.get("pyodide.asm.wasm")
    if expected and expected != wasm_sri:
        sys.exit("Checksum mismatch for pyodide.asm.wasm")
    for name in ("pyodide.js", "pyodide_py.tar", "packages.json"):
        f = dist_dir / manifest["dirs"]["wasm"] / name
        if f.exists():
            actual = sha384(f)
            expected = checksums.get(name)
            if expected and expected != actual:
                sys.exit(f"Checksum mismatch for {name}")
    out_html = out_html.replace(
        "</head>",
        (
            f'<link rel="preload" '
            f'href="{manifest["dirs"]["wasm"]}/pyodide.asm.wasm" '
            f'as="fetch" type="application/wasm" integrity="{wasm_sri}" '
            'crossorigin="anonymous" />\n</head>'
        ),
    )  # noqa: E501
else:
    wasm_sri = None
(dist_dir / "index.html").write_text(out_html)

wasm_llm_dir = ROOT / manifest["dirs"]["wasm_llm"]
if wasm_llm_dir.exists():
    f = dist_dir / manifest["dirs"]["wasm_llm"] / "wasm-gpt2.tar"
    if f.exists():
        actual = sha384(f)
        expected = checksums.get("wasm-gpt2.tar")
        if expected and expected != actual:
            sys.exit("Checksum mismatch for wasm-gpt2.tar")


# generate service worker
generate_service_worker(ROOT, dist_dir, manifest)
(dist_dir / "service-worker.js").write_bytes((dist_dir / "sw.js").read_bytes())
check_gzip_size(dist_dir / "insight.bundle.js")
