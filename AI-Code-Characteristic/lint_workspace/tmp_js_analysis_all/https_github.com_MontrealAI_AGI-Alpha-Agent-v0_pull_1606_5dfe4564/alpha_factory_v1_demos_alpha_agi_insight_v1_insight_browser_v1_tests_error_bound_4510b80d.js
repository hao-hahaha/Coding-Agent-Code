import test from 'node:test';
import assert from 'node:assert/strict';
import { initErrorBoundary, getErrorLog, clearErrorLog } from '../src/utils/errorBoundary.ts';

function makeMocks() {
  const store = {};
  global.localStorage = {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => {
      store[k] = String(v);
    },
    removeItem: (k) => {
      delete store[k];
    },
  };
  global.window = { toast() {} };
}

test('error log retains last 50 entries', () => {
  makeMocks();
  clearErrorLog();
  initErrorBoundary();
  for (let i = 1; i <= 55; i++) {
    window.onerror(`err${i}`, 'f.js', i, 0, new Error(String(i)));
  }
  const logs = getErrorLog();
  assert.equal(logs.length, 50);
  assert.equal(logs[0].message, 'err6');
  assert.equal(logs[49].message, 'err55');
});
