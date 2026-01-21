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

export function depthColor(depth, maxDepth) {
  const md = Math.max(1, maxDepth ?? depth ?? 1);
  const ratio = 1 - Math.min(depth ?? 0, md) / md;
  return `rgba(0,175,255,${ratio})`;
}
