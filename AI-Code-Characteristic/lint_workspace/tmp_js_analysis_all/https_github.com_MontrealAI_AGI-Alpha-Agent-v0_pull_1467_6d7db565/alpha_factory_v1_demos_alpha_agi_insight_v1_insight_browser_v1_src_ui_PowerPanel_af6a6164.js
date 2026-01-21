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
  const gpuLabel = document.createElement('label');
  const gpuToggle = document.createElement('input');
  gpuToggle.type = 'checkbox';
  gpuToggle.id = 'gpu-toggle';
  gpuLabel.appendChild(gpuToggle);
  gpuLabel.append(' GPU');
  panel.appendChild(gpuLabel);
  panel.appendChild(pre);
  try {
    const saved = localStorage.getItem('USE_GPU');
    gpuToggle.checked = saved !== '0';
  } catch {
    gpuToggle.checked = true;
  }
  window.USE_GPU = gpuToggle.checked && !!navigator.gpu;
  gpuToggle.addEventListener('change', () => {
    window.USE_GPU = gpuToggle.checked && !!navigator.gpu;
    try {
      localStorage.setItem('USE_GPU', gpuToggle.checked ? '1' : '0');
    } catch {}
  });
  document.body.appendChild(panel);
  function update(e) {
    pre.textContent = JSON.stringify(e, null, 2);
  }
  return { update, gpuToggle };
}
