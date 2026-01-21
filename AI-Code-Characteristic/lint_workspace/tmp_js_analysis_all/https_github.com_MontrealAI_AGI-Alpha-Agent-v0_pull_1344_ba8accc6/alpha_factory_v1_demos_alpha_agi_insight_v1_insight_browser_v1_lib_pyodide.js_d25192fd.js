// SPDX-License-Identifier: Apache-2.0
export async function loadPyodide(opts) {
  if (typeof window.loadPyodide === 'function') {
    return window.loadPyodide(opts);
  }
  throw new Error('pyodide.js not bundled');
}
