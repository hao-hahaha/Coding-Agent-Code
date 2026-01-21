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
  const list = document.createElement('ul');
  const table = document.createElement('table');
  panel.appendChild(list);
  panel.appendChild(table);
  document.body.appendChild(panel);

  async function render() {
    const runs = await archive.list();
    list.innerHTML = '';
    runs.forEach((r, idx) => {
      const li = document.createElement('li');
      li.textContent = `run ${idx + 1} gen ${r.gen}`;
      li.style.cursor = 'pointer';
      li.onclick = () => show(r);
      list.appendChild(li);
    });
  }

  function show(run) {
    table.innerHTML = '<tr><th>logic</th><th>feasible</th><th>strategy</th></tr>';
    for (const d of run.pop) {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${d.logic}</td><td>${d.feasible}</td><td>${d.strategy}</td>`;
      table.appendChild(tr);
    }
  }

  return { render, show };
}
