// SPDX-License-Identifier: Apache-2.0
export function initCriticPanel() {
  const root = document.createElement('div');
  root.id = 'critic-panel';
  root.setAttribute('role', 'region');
  root.setAttribute('aria-label', 'Critic');
  Object.assign(root.style, {
    position: 'fixed',
    top: '10px',
    right: '10px',
    background: 'rgba(0,0,0,0.7)',
    color: '#fff',
    padding: '8px',
    font: '14px sans-serif',
    display: 'none',
    zIndex: 1000,
  });

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '200');
  svg.setAttribute('height', '200');
  svg.id = 'critic-chart';

  const table = document.createElement('table');
  table.id = 'critic-table';
  table.style.marginTop = '4px';
  table.style.fontSize = '12px';

  root.appendChild(svg);
  root.appendChild(table);
  document.body.appendChild(root);

  let highlighted = null;

  function drawSpider(scores) {
    const labels = Object.keys(scores);
    const values = Object.values(scores);
    const size = 200;
    const center = size / 2;
    const radius = center - 20;
    const step = (Math.PI * 2) / labels.length;
    svg.innerHTML = '';
    const pts = [];
    labels.forEach((label, i) => {
      const angle = i * step - Math.PI / 2;
      const r = radius * (values[i] ?? 0);
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      pts.push(`${x},${y}`);
      const lx = center + radius * Math.cos(angle);
      const ly = center + radius * Math.sin(angle);
      const tx = center + (radius + 12) * Math.cos(angle);
      const ty = center + (radius + 12) * Math.sin(angle);
      const line = document.createElementNS('http://www.w3.org/2000/svg','line');
      line.setAttribute('x1', center);
      line.setAttribute('y1', center);
      line.setAttribute('x2', lx);
      line.setAttribute('y2', ly);
      line.setAttribute('stroke', '#ccc');
      svg.appendChild(line);
      const text = document.createElementNS('http://www.w3.org/2000/svg','text');
      text.setAttribute('x', tx);
      text.setAttribute('y', ty);
      text.setAttribute('font-size', '10');
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('dominant-baseline', 'middle');
      text.textContent = label;
      svg.appendChild(text);
    });
    const poly = document.createElementNS('http://www.w3.org/2000/svg','polygon');
    poly.setAttribute('points', pts.join(' '));
    poly.setAttribute('fill', 'rgba(0,100,250,0.3)');
    poly.setAttribute('stroke', 'blue');
    svg.appendChild(poly);
  }

  function show(scores, element) {
    if (highlighted) highlighted.removeAttribute('stroke');
    if (element) {
      element.setAttribute('stroke', 'yellow');
      highlighted = element;
    }
    drawSpider(scores);
    table.innerHTML = Object.entries(scores)
      .map(([k,v]) => `<tr><th>${k}</th><td>${v.toFixed(2)}</td></tr>`) 
      .join('');
    root.style.display = 'block';
  }

  return { show };
}
