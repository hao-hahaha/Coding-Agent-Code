// SPDX-License-Identifier: Apache-2.0
import { mutate } from '../src/evolve/mutate.js';
import { paretoFront } from '../src/utils/pareto.js';

function lcg(seed) {
  function rand() {
    seed = Math.imul(1664525, seed) + 1013904223 >>> 0;
    return seed / 2 ** 32;
  }
  rand.state = () => seed;
  rand.set = (s) => { seed = s >>> 0; };
  return rand;
}

function shuffle(arr, rand) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
}

self.onmessage = (ev) => {
  const { pop, rngState, mutations, popSize } = ev.data;
  const rand = lcg(0);
  rand.set(rngState);
  let next = mutate(pop, rand, mutations);
  const front = paretoFront(next);
  next.forEach((d) => (d.front = front.includes(d)));
  shuffle(next, rand);
  next = front.concat(next.slice(0, popSize - 10));
  self.postMessage({ pop: next, rngState: rand.state() });
};
