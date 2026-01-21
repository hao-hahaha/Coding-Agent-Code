// SPDX-License-Identifier: Apache-2.0
import { t } from '../ui/i18n.js';
let log = [];

export function initErrorBoundary() {
  try {
    log = JSON.parse(localStorage.getItem('errorLog') || '[]');
  } catch {
    log = [];
  }
  function record(entry) {
    log.push(entry);
    try {
      localStorage.setItem('errorLog', JSON.stringify(log));
    } catch {}
    if (window.toast) {
      window.toast(entry.message ? String(entry.message) : t('error_unknown'));
    }
  }
  window.onerror = (msg, url, line, col, err) => {
    record({
      type: 'error',
      message: String(msg),
      url: url || '',
      line: line || 0,
      column: col || 0,
      stack: err && err.stack,
      ts: Date.now(),
    });
  };
  window.onunhandledrejection = (ev) => {
    const reason = ev.reason || {};
    record({
      type: 'unhandledrejection',
      message: reason.message ? String(reason.message) : String(reason),
      stack: reason.stack,
      ts: Date.now(),
    });
  };
}

export function getErrorLog() {
  return log.slice();
}

export function clearErrorLog() {
  log = [];
  try {
    localStorage.removeItem('errorLog');
  } catch {}
}
