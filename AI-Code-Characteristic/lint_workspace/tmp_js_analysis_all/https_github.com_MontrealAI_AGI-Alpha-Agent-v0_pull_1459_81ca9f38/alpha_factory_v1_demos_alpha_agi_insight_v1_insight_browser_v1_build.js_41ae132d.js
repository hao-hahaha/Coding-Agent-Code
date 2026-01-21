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
    outfile: `${OUT_DIR}/app.js`,
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
  const appSri = await sha384('app.js');
  const styleSri = await sha384('style.css');
  let outHtml = html
    .replace(
      '<script type="module" src="app.js" crossorigin="anonymous"></script>',
      `<script type="module" src="app.js" integrity="${appSri}" crossorigin="anonymous"></script>`
    )
    .replace(
      'href="style.css"',
      `href="style.css" integrity="${styleSri}" crossorigin="anonymous"`
    )
    .replace('src/ui/controls.css', 'controls.css');
  const csp =
    "default-src 'self'; connect-src 'self' https://api.openai.com" +
    (ipfsOrigin ? ` ${ipfsOrigin}` : '') +
    (otelOrigin ? ` ${otelOrigin}` : '') +
    "; script-src 'self' 'wasm-unsafe-eval'";
  outHtml = outHtml.replace(
    /<meta[^>]*http-equiv="Content-Security-Policy"[^>]*>/,
    `<meta http-equiv="Content-Security-Policy" content="${csp}" />`
  );
  await fs.copyFile('src/ui/controls.css', `${OUT_DIR}/controls.css`);
  await fs.copyFile('d3.v7.min.js', `${OUT_DIR}/d3.v7.min.js`);
  await fs.copyFile('lib/bundle.esm.min.js', `${OUT_DIR}/bundle.esm.min.js`);
  await fs.copyFile('lib/pyodide.js', `${OUT_DIR}/pyodide.js`);
  await fs.mkdir(`${OUT_DIR}/worker`, { recursive: true });
  await fs.copyFile('worker/evolver.js', `${OUT_DIR}/worker/evolver.js`);
  await fs.copyFile('worker/arenaWorker.js', `${OUT_DIR}/worker/arenaWorker.js`);
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

  outHtml = outHtml.replace(
    '</body>',
    `<script src="bundle.esm.min.js" integrity="${bundleSri}" crossorigin="anonymous"></script>\n` +
    `<script src="pyodide.js" integrity="${pyodideSri}" crossorigin="anonymous"></script>\n` +
    `${envScript}\n</body>`
  );
  await fs.mkdir(`${OUT_DIR}/wasm`, { recursive: true });
  for (const f of await fs.readdir('wasm')) {
    await fs.copyFile(`wasm/${f}`, `${OUT_DIR}/wasm/${f}`);
  }
  const wasmSri = await sha384('wasm/pyodide.asm.wasm');
  if (checksums['pyodide.asm.wasm'] && checksums['pyodide.asm.wasm'] !== wasmSri) {
    throw new Error('Checksum mismatch for pyodide.asm.wasm');
  }
  outHtml = outHtml.replace(
    '</head>',
    `<link rel="preload" href="wasm/pyodide.asm.wasm" as="fetch" type="application/wasm" integrity="${wasmSri}" crossorigin="anonymous" />\n</head>`
  );
  await fs.writeFile(`${OUT_DIR}/index.html`, outHtml);
  await fs.mkdir(`${OUT_DIR}/wasm_llm`, { recursive: true }).catch(() => {});
  for await (const f of await fs.readdir('wasm_llm')) {
    await fs.copyFile(`wasm_llm/${f}`, `${OUT_DIR}/wasm_llm/${f}`);
  }
  await injectManifest({
    swSrc: 'sw.js',
    swDest: `${OUT_DIR}/sw.js`,
    globDirectory: OUT_DIR,
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
      'src/i18n/*.json',
    ],
  });
  const size = await gzipSize.file(`${OUT_DIR}/app.js`);
  const MAX_GZIP_SIZE = 6 * 1024 * 1024; // 6 MiB
  if (size > MAX_GZIP_SIZE) {
    throw new Error(`gzip size ${size} bytes exceeds limit`);
  }
  if (process.env.WEB3_STORAGE_TOKEN) {
    const client = new Web3Storage({ token: process.env.WEB3_STORAGE_TOKEN });
    const files = await Promise.all([
      'index.html', 'app.js', 'style.css', 'd3.v7.min.js', 'bundle.esm.min.js'
    ].map(async f => new File([await fs.readFile(`${OUT_DIR}/${f}`)], f)));
    const cid = await client.put(files, { wrapWithDirectory: false });
    await fs.writeFile(`${OUT_DIR}/CID.txt`, cid);
    if (verbose) {
      console.log('Pinned CID:', cid);
    }
  }
}

bundle().catch(err => { console.error(err); process.exit(1); });
