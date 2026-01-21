#!/usr/bin/env node
// SPDX-License-Identifier: Apache-2.0
import { build } from 'esbuild';
import { promises as fs } from 'fs';
import { execSync } from 'child_process';
import gzipSize from 'gzip-size';
import { Web3Storage, File } from 'web3.storage';

const OUT_DIR = 'dist';

async function bundle() {
  const html = await fs.readFile('index.html', 'utf8');
  const match = html.match(/<script type="module">([\s\S]*?)<\/script>/);
  if (!match) throw new Error('inline script not found');
  await fs.writeFile('tmp.js', match[1]);
  await fs.mkdir(OUT_DIR, { recursive: true });
  await build({ entryPoints: ['tmp.js'], bundle: true, minify: true, outfile: `${OUT_DIR}/app.js` });
  await fs.unlink('tmp.js');
  const outHtml = html
    .replace(match[0], '<script src="app.js"></script>')
    .replace('src/ui/controls.css', 'controls.css');
  await fs.writeFile(`${OUT_DIR}/index.html`, outHtml);
  execSync(
    `npx tailwindcss -i style.css -o ${OUT_DIR}/style.css --minify`,
    { stdio: 'inherit' }
  );
  await fs.copyFile('src/ui/controls.css', `${OUT_DIR}/controls.css`);
  await fs.copyFile('d3.v7.min.js', `${OUT_DIR}/d3.v7.min.js`);
  await fs.copyFile('lib/bundle.esm.min.js', `${OUT_DIR}/bundle.esm.min.js`);
  await fs.copyFile('lib/pyodide.js', `${OUT_DIR}/pyodide.js`);
  await fs.mkdir(`${OUT_DIR}/wasm`, { recursive: true });
  for (const f of await fs.readdir('wasm')) {
    await fs.copyFile(`wasm/${f}`, `${OUT_DIR}/wasm/${f}`);
  }
  await fs.mkdir(`${OUT_DIR}/wasm_llm`, { recursive: true }).catch(() => {});
  for await (const f of await fs.readdir('wasm_llm')) {
    await fs.copyFile(`wasm_llm/${f}`, `${OUT_DIR}/wasm_llm/${f}`);
  }
  const size = await gzipSize.file(`${OUT_DIR}/app.js`);
  if (size > 180 * 1024) {
    throw new Error(`gzip size ${size} bytes exceeds limit`);
  }
  if (process.env.WEB3_STORAGE_TOKEN) {
    const client = new Web3Storage({ token: process.env.WEB3_STORAGE_TOKEN });
    const files = await Promise.all([
      'index.html', 'app.js', 'style.css', 'd3.v7.min.js', 'bundle.esm.min.js'
    ].map(async f => new File([await fs.readFile(`${OUT_DIR}/${f}`)], f)));
    const cid = await client.put(files, { wrapWithDirectory: false });
    await fs.writeFile(`${OUT_DIR}/CID.txt`, cid);
    console.log('Pinned CID:', cid);
  }
}

bundle().catch(err => { console.error(err); process.exit(1); });
