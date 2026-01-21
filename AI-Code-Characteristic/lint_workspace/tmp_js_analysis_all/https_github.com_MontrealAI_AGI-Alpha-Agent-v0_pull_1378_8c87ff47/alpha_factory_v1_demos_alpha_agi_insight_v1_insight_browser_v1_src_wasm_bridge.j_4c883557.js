// SPDX-License-Identifier: Apache-2.0
import { loadPyodide } from '../lib/pyodide.js';

let pyodideReady;
async function initPy() {
  if (!pyodideReady) {
    try {
      pyodideReady = await loadPyodide({ indexURL: './wasm/' });
    } catch (err) {
      toast('Pyodide failed to load');
      return Promise.reject(err);
    }
  }
  return pyodideReady;
}

export async function run(params = {}) {
  const pyodide = await initPy();
  const seed = params.seed ?? 0;
  await pyodide.runPythonAsync(`import random; random.seed(${seed})`);
  const code = `\nfrom forecast import forecast_disruptions\nfrom simulation import sector\nres = forecast_disruptions([sector.Sector('x')], 1, seed=${seed})\nimport json\nprint(json.dumps([{'year': r.year, 'capability': r.capability} for r in res]))`;
  await pyodide.runPythonAsync('import forecast, mats');
  const out = pyodide.runPython(code);
  return JSON.parse(out);
}

window.Insight = { run };
