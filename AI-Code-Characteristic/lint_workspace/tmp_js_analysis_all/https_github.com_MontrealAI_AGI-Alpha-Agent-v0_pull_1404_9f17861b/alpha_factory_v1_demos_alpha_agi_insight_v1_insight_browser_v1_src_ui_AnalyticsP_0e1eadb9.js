// SPDX-License-Identifier: Apache-2.0
export function initAnalyticsPanel() {
  const panel = document.createElement('div');
  panel.id = 'analytics-panel';
  Object.assign(panel.style, {
    position: 'fixed',
    top: '10px',
    right: '220px',
    background: 'rgba(0,0,0,0.7)',
    color: '#fff',
    padding: '4px',
    fontSize: '12px',
    zIndex: 1000,
  });
  const canvas = document.createElement('canvas');
  canvas.width = 200;
  canvas.height = 100;
  panel.appendChild(canvas);
  document.body.appendChild(panel);
  const ctx = canvas.getContext('2d');
  function update(pop, gen) {
    if (!ctx) return;
    const bins = new Map();
    for (const d of pop) {
      const h = Math.round(d.horizonYears || 0);
      bins.set(h, (bins.get(h) || 0) + 1);
    }
    const keys = Array.from(bins.keys()).sort((a, b) => a - b);
    const max = Math.max(...bins.values(), 1);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const barW = canvas.width / keys.length;
    keys.forEach((k, i) => {
      const v = bins.get(k) || 0;
      const hgt = (canvas.height - 15) * (v / max);
      ctx.fillStyle = 'steelblue';
      ctx.fillRect(i * barW, canvas.height - hgt, barW - 2, hgt);
      ctx.fillStyle = '#fff';
      ctx.fillText(String(k), i * barW + barW / 2 - 4, canvas.height - 2);
    });
    ctx.fillStyle = '#fff';
    ctx.fillText(`gen ${gen}`, 4, 10);
  }
  return { update };
}
