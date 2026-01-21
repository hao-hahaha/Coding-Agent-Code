// SPDX-License-Identifier: Apache-2.0
export function initFpsMeter(isRunning) {
  if (document.getElementById('fps-meter')) return;
  const el = document.createElement('div');
  el.id = 'fps-meter';
  el.setAttribute('role', 'status');
  el.setAttribute('aria-live', 'polite');
  Object.assign(el.style, {
    position: 'fixed',
    right: '4px',
    bottom: '4px',
    background: 'rgba(0,0,0,0.6)',
    color: '#0f0',
    fontFamily: 'monospace',
    fontSize: '12px',
    padding: '2px 4px',
    zIndex: 1000
  });
  document.body.appendChild(el);
  let last = 0;
  function frame(ts) {
    if (isRunning()) {
      if (last) {
        const fps = 1000 / (ts - last);
        el.textContent = `${fps.toFixed(1)} fps`;
      }
      last = ts;
    } else {
      last = ts;
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
