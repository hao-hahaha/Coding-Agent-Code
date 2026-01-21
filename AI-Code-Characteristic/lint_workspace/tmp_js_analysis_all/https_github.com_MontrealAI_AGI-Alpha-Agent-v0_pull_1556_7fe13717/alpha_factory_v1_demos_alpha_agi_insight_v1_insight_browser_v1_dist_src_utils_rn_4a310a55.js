// SPDX-License-Identifier: Apache-2.0
export function lcg(seed) {
  function rand() {
    seed = Math.imul(1664525, seed) + 1013904223 >>> 0;
    return seed / 2 ** 32;
  }
  rand.state = () => seed;
  rand.set = (s) => { seed = s >>> 0; };
  return rand;
}
