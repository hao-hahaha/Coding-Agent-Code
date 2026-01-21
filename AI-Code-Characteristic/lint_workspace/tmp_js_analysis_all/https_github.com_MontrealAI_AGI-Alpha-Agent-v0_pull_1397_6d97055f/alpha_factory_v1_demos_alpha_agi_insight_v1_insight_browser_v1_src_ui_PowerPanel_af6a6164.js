// SPDX-License-Identifier: Apache-2.0
export function initPowerPanel() {
  const panel = document.createElement('div');
  panel.id = 'power-panel';
  Object.assign(panel.style, {
    position: 'fixed',
    top: '10px',
    left: '10px',
    background: 'rgba(0,0,0,0.7)',
    color: '#fff',
    padding: '8px',
    fontSize: '12px',
    zIndex: 1000,
    whiteSpace: 'pre',
  });
  const pre = document.createElement('pre');
  panel.appendChild(pre);
  document.body.appendChild(panel);
  function update(e) {
    pre.textContent = JSON.stringify(e, null, 2);
  }
  return { update };
}
