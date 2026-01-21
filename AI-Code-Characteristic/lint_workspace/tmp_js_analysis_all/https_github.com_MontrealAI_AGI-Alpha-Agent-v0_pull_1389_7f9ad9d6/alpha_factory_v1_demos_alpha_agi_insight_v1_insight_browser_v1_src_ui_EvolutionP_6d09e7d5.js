// SPDX-License-Identifier: Apache-2.0
export function initEvolutionPanel(archive) {
  const panel = document.createElement('div');
  panel.id = 'evolution-panel';
  Object.assign(panel.style, {
    position: 'fixed',
    bottom: '10px',
    left: '10px',
    background: 'rgba(0,0,0,0.7)',
    color: '#fff',
    padding: '8px',
    fontSize: '12px',
    zIndex: 1000,
    maxHeight: '40vh',
    overflowY: 'auto',
  });
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '200');
  svg.setAttribute('height', '100');
  const table = document.createElement('table');
  const header = document.createElement('tr');
  header.innerHTML =
    '<th data-k="seed">Seed</th><th data-k="score">Score</th><th data-k="novelty">Novelty</th><th data-k="timestamp">Time</th><th></th>';
  table.appendChild(header);
  panel.appendChild(svg);
  panel.appendChild(table);
  document.body.appendChild(panel);

  let sortKey = 'timestamp';
  let desc = true;
  header.querySelectorAll('th[data-k]').forEach((th) => {
    th.style.cursor = 'pointer';
    th.onclick = () => {
      const k = th.dataset.k;
      if (sortKey === k) desc = !desc;
      else {
        sortKey = k;
        desc = true;
      }
      render();
    };
  });

  function respawn(seed) {
    const q = new URLSearchParams(window.location.hash.replace(/^#\/?/, ''));
    q.set('s', seed);
    window.location.hash = '#/' + q.toString();
  }

  function drawTree(runs) {
    svg.innerHTML = '';
    const pos = new Map();
    runs.forEach((r, i) => {
      const x = 20 + i * 20;
      const y = 20;
      pos.set(r.id, { x, y });
      const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      c.setAttribute('cx', String(x));
      c.setAttribute('cy', String(y));
      c.setAttribute('r', '4');
      c.setAttribute('fill', 'white');
      svg.appendChild(c);
    });
    runs.forEach((r) => {
      const child = pos.get(r.id);
      if (!child) return;
      for (const p of r.parents || []) {
        const parent = pos.get(p);
        if (!parent) continue;
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', String(parent.x));
        line.setAttribute('y1', String(parent.y));
        line.setAttribute('x2', String(child.x));
        line.setAttribute('y2', String(child.y));
        line.setAttribute('stroke', 'white');
        svg.appendChild(line);
      }
    });
  }

  async function render() {
    const runs = await archive.list();
    runs.sort((a, b) => (desc ? b[sortKey] - a[sortKey] : a[sortKey] - b[sortKey]));
    table.querySelectorAll('tr').forEach((tr, i) => { if (i) tr.remove(); });
    runs.forEach((r) => {
      const tr = document.createElement('tr');
      const time = new Date(r.timestamp).toLocaleTimeString();
      tr.innerHTML = `<td>${r.seed}</td><td>${r.score.toFixed(2)}</td><td>${r.novelty.toFixed(2)}</td><td>${time}</td>`;
      const td = document.createElement('td');
      const btn = document.createElement('button');
      btn.textContent = 'Re-spawn';
      btn.onclick = () => respawn(r.seed);
      td.appendChild(btn);
      tr.appendChild(td);
      table.appendChild(tr);
    });
    drawTree(runs);
  }

  return { render };
}
