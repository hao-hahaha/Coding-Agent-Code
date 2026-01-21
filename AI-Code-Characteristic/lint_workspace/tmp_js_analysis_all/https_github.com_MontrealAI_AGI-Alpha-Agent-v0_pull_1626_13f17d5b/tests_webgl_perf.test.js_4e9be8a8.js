import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const dist = resolve(__dirname, 'alpha_factory_v1/demos/alpha_agi_insight_v1/insight_browser_v1/dist/index.html');

async function measureFps(page) {
  await page.waitForSelector('#fps-meter');
  await page.waitForTimeout(2000);
  const text = await page.innerText('#fps-meter');
  return parseFloat(text.split(/[\s]/)[0]);
}

test('webgl renderer maintains 60fps with 5k points', async () => {
  const url = dist + '#seed=1&pop=5000&gen=1';
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto(url);
  const fps = await measureFps(page);
  await browser.close();
  assert.ok(fps >= 60, `fps=${fps}`);
});
