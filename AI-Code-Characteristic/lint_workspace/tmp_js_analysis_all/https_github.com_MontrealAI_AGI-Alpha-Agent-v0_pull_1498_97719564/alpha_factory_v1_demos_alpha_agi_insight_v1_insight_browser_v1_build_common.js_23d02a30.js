// SPDX-License-Identifier: Apache-2.0
import { promises as fs } from 'fs';
import fsSync from 'fs';
import path from 'path';

export async function copyAssets(manifest, repoRoot, outDir) {
  for (const rel of manifest.files) {
    const dest = path.join(outDir, rel);
    await fs.mkdir(path.dirname(dest), { recursive: true });
    await fs.copyFile(rel, dest).catch(() => {});
  }
  const i18nDir = manifest.dirs.translations;
  if (fsSync.existsSync(i18nDir)) {
    await fs.mkdir(path.join(outDir, i18nDir), { recursive: true });
    for (const f of await fs.readdir(i18nDir)) {
      await fs.copyFile(path.join(i18nDir, f), path.join(outDir, i18nDir, f));
    }
  }
  const criticsSrc = path.join(repoRoot, manifest.dirs.critics);
  if (fsSync.existsSync(criticsSrc)) {
    await fs.mkdir(path.join(outDir, manifest.dirs.critics), { recursive: true });
    for (const f of await fs.readdir(criticsSrc)) {
      await fs.copyFile(path.join(criticsSrc, f), path.join(outDir, manifest.dirs.critics, f));
    }
  }
  for (const dirKey of ['wasm', 'wasm_llm']) {
    const dir = manifest.dirs[dirKey];
    if (fsSync.existsSync(dir)) {
      await fs.mkdir(path.join(outDir, dir), { recursive: true });
      for (const f of await fs.readdir(dir)) {
        await fs.copyFile(path.join(dir, f), path.join(outDir, dir, f));
      }
    }
  }
}

export function injectEnv(env) {
  const script = `<script>window.PINNER_TOKEN=${JSON.stringify(env.PINNER_TOKEN || '')};window.OPENAI_API_KEY=${JSON.stringify(env.OPENAI_API_KEY || '')};window.OTEL_ENDPOINT=${JSON.stringify(env.OTEL_ENDPOINT || '')};window.IPFS_GATEWAY=${JSON.stringify(env.IPFS_GATEWAY || '')};</script>`;
  return script;
}
