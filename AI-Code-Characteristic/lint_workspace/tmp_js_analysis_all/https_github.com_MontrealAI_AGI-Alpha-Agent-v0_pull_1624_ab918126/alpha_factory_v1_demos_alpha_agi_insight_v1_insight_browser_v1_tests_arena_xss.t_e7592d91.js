// SPDX-License-Identifier: Apache-2.0
import test from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
import { initArenaPanel } from '../src/ui/ArenaPanel.ts';

test('ArenaPanel escapes HTML input', () => {
  const dom = new JSDOM('<!doctype html><body></body>', { runScripts: 'dangerously' });
  global.document = dom.window.document;
  global.window = dom.window;

  const panel = initArenaPanel();
  let alerted = false;
  dom.window.alert = () => {
    alerted = true;
  };

  const payload = '<img src=x onerror=alert(1)>';
  panel.show([{ role: 'user', text: payload }], 0);

  const item = dom.window.document.querySelector('#debate-panel ul li');
  assert(item);
  assert.ok(item.innerHTML.includes('&lt;img'));
  assert.equal(alerted, false);
});
