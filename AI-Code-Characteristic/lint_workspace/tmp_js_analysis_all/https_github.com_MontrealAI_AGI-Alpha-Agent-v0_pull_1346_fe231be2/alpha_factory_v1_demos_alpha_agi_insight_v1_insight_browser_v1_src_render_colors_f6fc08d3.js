// SPDX-License-Identifier: Apache-2.0
export const strategyColors = {
  gaussian: '#ff7f0e',
  swap: '#2ca02c',
  jump: '#d62728',
  scramble: '#9467bd',
  front: '#00afff',
  base: '#666',
};

export function credibilityColor(v) {
  const clamped = Math.max(0, Math.min(1, v ?? 0));
  const hue = 120 * clamped; // red -> green
  return `hsl(${hue},70%,50%)`;
}
