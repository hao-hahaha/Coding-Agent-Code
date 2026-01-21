// SPDX-License-Identifier: Apache-2.0
import { t } from './i18n.js';

export function initArenaPanel(onDebate) {
  const root = document.createElement('details');
  root.id = 'arena-panel';
  Object.assign(root.style, {
    position: 'fixed',
    bottom: '10px',
    right: '220px',
    background: 'rgba(0,0,0,0.7)',
    color: '#fff',
    padding: '8px',
    fontSize: '12px',
    zIndex: 1000,
    maxHeight: '40vh',
    overflowY: 'auto',
  });
  const summary = document.createElement('summary');
  summary.textContent = t('summary.debateArena');
  const ranking = document.createElement('ul');
  ranking.id = 'ranking';
  const panel = document.createElement('div');
  panel.id = 'debate-panel';
  const msgs = document.createElement('ul');
  panel.appendChild(msgs);
  root.appendChild(summary);
  root.appendChild(ranking);
  root.appendChild(panel);
  document.body.appendChild(root);

  let currentFront = [];

  function render(front) {
    currentFront = front;
    ranking.innerHTML = '';
    const sorted = [...front].sort((a, b) => (b.rank ?? 0) - (a.rank ?? 0));
    sorted.forEach((p) => {
      const li = document.createElement('li');
      li.textContent = `${t('label.rank')} ${(p.rank ?? 0).toFixed(1)} `;
      const btn = document.createElement('button');
      btn.textContent = t('summary.debate');
      btn.addEventListener('click', () => onDebate?.(p));
      li.appendChild(btn);
      ranking.appendChild(li);
    });
  }

  function show(messages, score) {
    msgs.innerHTML = messages
      .map((m) => `<li><strong>${m.role}:</strong> ${m.text}</li>`)
      .join('');
    const li = document.createElement('li');
    li.textContent = `${t('label.score')}: ${score}`;
    msgs.appendChild(li);
    root.open = true;
  }

  return { render, show };
}
