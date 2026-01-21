// SPDX-License-Identifier: Apache-2.0
export function detectColdZone(points, bins = 10) {
  const hist = new Map();
  for (const [x, y] of points) {
    const cx = Math.max(0, Math.min(bins - 1, Math.floor(x * bins)));
    const cy = Math.max(0, Math.min(bins - 1, Math.floor(y * bins)));
    const key = `${cx}-${cy}`;
    hist.set(key, (hist.get(key) || 0) + 1);
  }
  let min = Infinity;
  let cell = '0-0';
  for (let i = 0; i < bins; i++) {
    for (let j = 0; j < bins; j++) {
      const key = `${i}-${j}`;
      const v = hist.get(key) || 0;
      if (v < min) {
        min = v;
        cell = key;
      }
    }
  }
  const [cx, cy] = cell.split('-').map(Number);
  return { x: cx, y: cy, count: min };
}
