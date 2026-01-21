// SPDX-License-Identifier: Apache-2.0
import { mutate } from '../src/evolve/mutate.js';
import { paretoFront } from '../src/utils/pareto.js';
import { lcg } from '../src/utils/rng.js';

const ua = self.navigator?.userAgent ?? '';
const isSafari = /Safari/.test(ua) && !/Chrome|Chromium|Edge/.test(ua);
const isIOS = /(iPad|iPhone|iPod)/.test(ua);
let pyReady;
let warned = false;
let pySupported = !(isSafari || isIOS);

async function loadPy() {
  if (!pySupported) {
    if (!warned) {
      self.postMessage({ toast: 'Pyodide unavailable; using JS only' });
      warned = true;
    }
    return null;
  }
  if (!pyReady) {
    try {
      const mod = await import('../src/wasm/bridge.js');
      pyReady = mod.initPy ? mod.initPy() : null;
    } catch {
      pyReady = null;
      pySupported = false;
      if (!warned) {
        self.postMessage({ toast: 'Pyodide failed to load; using JS only' });
        warned = true;
      }
    }
  }
  return pyReady;
}

function shuffle(arr, rand) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

self.onmessage = async (ev) => {
  const { pop, rngState, mutations, popSize, critic, gen, adaptive } = ev.data;
  const rand = lcg(0);
  rand.set(rngState);
  let next = mutate(pop, rand, mutations, gen, adaptive);
  const front = paretoFront(next);
  next.forEach((d) => (d.front = front.includes(d)));
  if (critic === 'llm') {
    await loadPy();
  }
  shuffle(next, rand);
  next = front.concat(next.slice(0, popSize - 10));
  const metrics = {
    avgLogic: next.reduce((s, d) => s + (d.logic ?? 0), 0) / next.length,
    avgFeasible: next.reduce((s, d) => s + (d.feasible ?? 0), 0) / next.length,
    frontSize: front.length,
  };
  self.postMessage({ pop: next, rngState: rand.state(), front, metrics });
};
