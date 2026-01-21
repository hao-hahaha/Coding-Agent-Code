#!/usr/bin/env node
// SPDX-License-Identifier: Apache-2.0
import { promises as fs } from 'fs';
import fsSync from 'fs';
import { execSync, spawnSync } from 'child_process';
import { createHash } from 'crypto';
import path from 'path';
import { fileURLToPath } from 'url';

const [major] = process.versions.node.split('.').map(Number);
if (major < 20) {
  console.error(
    `Node.js 20+ is required. Current version: ${process.versions.node}`
  );
  process.exit(1);
}

const { build } = await import('esbuild');
const gzipSize = (await import('gzip-size')).default;
const { Web3Storage, File } = await import('web3.storage');
const { injectManifest } = await import('workbox-build');
const dotenv = (await import('dotenv')).default;
dotenv.config();

const verbose = process.argv.includes('--verbose');

try {
  execSync('tsc --noEmit', { stdio: 'inherit' });
} catch (err) {
  process.exit(1);
}

const scriptPath = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(scriptPath), '..', '..', '..', '..');
const aliasRoot = path.join(repoRoot, 'src');
const aliasPlugin = {
  name: 'alias',
  setup(build) {
    build.onResolve({ filter: /^@insight-src\// }, args => ({
      path: path.join(aliasRoot, args.path.slice('@insight-src/'.length)),
    }));
  },
};

async function ensureWeb3Bundle() {
  const bundlePath = path.join('lib', 'bundle.esm.min.js');
  const data = await fs.readFile(bundlePath, 'utf8').catch(() => {
    throw new Error(
      'lib/bundle.esm.min.js missing. Run scripts/fetch_assets.py to download assets.'
    );
  });
  if (data.includes('Placeholder for web3.storage bundle.esm.min.js')) {
    throw new Error(
      'lib/bundle.esm.min.js is a placeholder. Run scripts/fetch_assets.py to download assets.'
    );
  }
}

function assetPaths() {
  const py = `import ast, json, pathlib
txt = pathlib.Path('scripts/fetch_assets.py').read_text()
tree = ast.parse(txt)
assets = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if getattr(t, 'id', None) == 'ASSETS':
                assets = ast.literal_eval(node.value)
print(json.dumps(list(assets.keys())))`;
  const proc = spawnSync('python', ['-'], {
    input: py,
    cwd: repoRoot,
    encoding: 'utf8',
  });
  if (proc.error) throw proc.error;
  if (proc.status !== 0) {
    throw new Error(proc.stderr);
  }
  return JSON.parse(proc.stdout.trim());
}

function expectedChecksums() {
  const py = `import ast, json, pathlib
txt = pathlib.Path('scripts/fetch_assets.py').read_text()
tree = ast.parse(txt)
checks = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if getattr(t, 'id', None) == 'CHECKSUMS':
                checks = ast.literal_eval(node.value)
print(json.dumps(checks))`;
  const proc = spawnSync('python', ['-'], {
    input: py,
    cwd: repoRoot,
    encoding: 'utf8',
  });
  if (proc.error) throw proc.error;
  if (proc.status !== 0) {
    throw new Error(proc.stderr);
  }
  return JSON.parse(proc.stdout.trim());
}

function ensureAssets() {
  for (const rel of assetPaths()) {
    const p = path.join(path.dirname(scriptPath), rel);
    if (!fsSync.existsSync(p)) continue;
    const data = fsSync.readFileSync(p, 'utf8');
    if (data.includes('placeholder')) {
      throw new Error(`${rel} contains placeholder text. Run scripts/fetch_assets.py to download assets.`);
    }
  }
}

const OUT_DIR = 'dist';

async function bundle() {
  const html = await fs.readFile('index.html', 'utf8');
  await ensureWeb3Bundle();
  ensureAssets();
  const checksums = expectedChecksums();
  const ipfsOrigin = process.env.IPFS_GATEWAY
    ? new URL(process.env.IPFS_GATEWAY).origin
    : '';
  const otelOrigin = process.env.OTEL_ENDPOINT
    ? new URL(process.env.OTEL_ENDPOINT).origin
    : '';
  await fs.mkdir(OUT_DIR, { recursive: true });
  await build({
    entryPoints: ['app.js'],
    bundle: true,
    minify: true,
    format: 'esm',
    target: 'es2020',
    outfile: `${OUT_DIR}/insight.bundle.js`,
    plugins: [aliasPlugin],
  });
  execSync(
    `npx tailwindcss -i style.css -o ${OUT_DIR}/style.css --minify`,
    { stdio: 'inherit' }
  );
  const sha384 = async (file) => {
    const data = await fs.readFile(`${OUT_DIR}/${file}`);
    return 'sha384-' + createHash('sha384').update(data).digest('base64');
  };
  const appSri = await sha384('insight.bundle.js');
  let outHtml = html.replace(
      '<script type="module" src="insight.bundle.js" crossorigin="anonymous"></script>',
      `<script type="module" src="insight.bundle.js" integrity="${appSri}" crossorigin="anonymous"></script>`
    );
  const csp =
    "default-src 'self'; connect-src 'self' https://api.openai.com" +
    (ipfsOrigin ? ` ${ipfsOrigin}` : '') +
    (otelOrigin ? ` ${otelOrigin}` : '') +
    "; script-src 'self' 'wasm-unsafe-eval'";
  outHtml = outHtml.replace(
    /<meta[^>]*http-equiv="Content-Security-Policy"[^>]*>/,
    `<meta http-equiv="Content-Security-Policy" content="${csp}" />`
  );
  await fs.copyFile('d3.v7.min.js', `${OUT_DIR}/d3.v7.min.js`);
  await fs.copyFile('lib/bundle.esm.min.js', `${OUT_DIR}/bundle.esm.min.js`);
  await fs.copyFile('lib/pyodide.js', `${OUT_DIR}/pyodide.js`);
  await fs.mkdir(`${OUT_DIR}/src/utils`, { recursive: true });
  await fs.copyFile('src/utils/rng.js', `${OUT_DIR}/src/utils/rng.js`);
  await fs.mkdir(`${OUT_DIR}/src/i18n`, { recursive: true });
  for (const f of await fs.readdir('src/i18n')) {
    await fs.copyFile(`src/i18n/${f}`, `${OUT_DIR}/src/i18n/${f}`);
  }
  await fs.copyFile('sw.js', `${OUT_DIR}/sw.js`).catch(() => {});
  await fs.copyFile('manifest.json', `${OUT_DIR}/manifest.json`).catch(() => {});
  await fs.copyFile('favicon.svg', `${OUT_DIR}/favicon.svg`).catch(() => {});
  await fs.mkdir(`${OUT_DIR}/data/critics`, { recursive: true });
  try {
    for (const f of await fs.readdir('../../../../data/critics')) {
      await fs.copyFile(
        `../../../../data/critics/${f}`,
        `${OUT_DIR}/data/critics/${f}`
      );
    }
  } catch {}
  const bundleSri = await sha384('bundle.esm.min.js');
  const pyodideSri = await sha384('pyodide.js');

  const envScript = `<script>window.PINNER_TOKEN=${JSON.stringify(
    process.env.PINNER_TOKEN || ''
  )};window.OPENAI_API_KEY=${JSON.stringify(
    process.env.OPENAI_API_KEY || ''
  )};window.OTEL_ENDPOINT=${JSON.stringify(
    process.env.OTEL_ENDPOINT || ''
  )};window.IPFS_GATEWAY=${JSON.stringify(
    process.env.IPFS_GATEWAY || ''
  )};</script>`;

  const wasmBase64 = fsSync.readFileSync('wasm/pyodide.asm.wasm').toString('base64');
  let gpt2Base64 = '';
  try {
    gpt2Base64 = fsSync.readFileSync('wasm_llm/wasm-gpt2.tar').toString('base64');
  } catch {}
  const bundlePath = `${OUT_DIR}/insight.bundle.js`;
  let bundleText = await fs.readFile(bundlePath, 'utf8');
  bundleText = `window.PYODIDE_WASM_BASE64='${wasmBase64}';window.GPT2_MODEL_BASE64='${gpt2Base64}';\n` + bundleText;
  await fs.writeFile(bundlePath, bundleText);
  outHtml = outHtml.replace(
    '</body>',
    `<script src="bundle.esm.min.js" integrity="${bundleSri}" crossorigin="anonymous"></script>\n` +
    `<script src="pyodide.js" integrity="${pyodideSri}" crossorigin="anonymous"></script>\n` +
    `${envScript}\n</body>`
  );
  await fs.writeFile(`${OUT_DIR}/index.html`, outHtml);
  await injectManifest({
    swSrc: 'sw.js',
    swDest: `${OUT_DIR}/sw.js`,
    globDirectory: OUT_DIR,
    globPatterns: [
      'index.html',
      'insight.bundle.js',
      'd3.v7.min.js',
      'pyodide.*',
      'data/critics/*',
      'src/i18n/*.json',
    ],
  });
  const size = await gzipSize.file(`${OUT_DIR}/insight.bundle.js`);
  const MAX_GZIP_SIZE = 6 * 1024 * 1024; // 6 MiB
  if (size > MAX_GZIP_SIZE) {
    throw new Error(`gzip size ${size} bytes exceeds limit`);
  }
  if (process.env.WEB3_STORAGE_TOKEN) {
    const client = new Web3Storage({ token: process.env.WEB3_STORAGE_TOKEN });
    const files = await Promise.all([
      'index.html', 'insight.bundle.js', 'd3.v7.min.js', 'bundle.esm.min.js'
    ].map(async f => new File([await fs.readFile(`${OUT_DIR}/${f}`)], f)));
    const cid = await client.put(files, { wrapWithDirectory: false });
    await fs.writeFile(`${OUT_DIR}/CID.txt`, cid);
    if (verbose) {
      console.log('Pinned CID:', cid);
    }
  }
}

bundle().catch(err => { console.error(err); process.exit(1); });
