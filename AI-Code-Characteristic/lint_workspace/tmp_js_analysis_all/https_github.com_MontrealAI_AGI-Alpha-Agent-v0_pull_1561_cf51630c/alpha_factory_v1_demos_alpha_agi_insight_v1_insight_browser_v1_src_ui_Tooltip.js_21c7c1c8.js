// SPDX-License-Identifier: Apache-2.0
export function showTooltip(x, y, text) {
  let tip = document.getElementById('tooltip');
  if (!tip) {
    tip = document.createElement('div');
    tip.id = 'tooltip';
    tip.setAttribute('role', 'tooltip');
    tip.style.position = 'absolute';
    tip.style.pointerEvents = 'none';
    tip.style.background = 'rgba(0,0,0,0.7)';
    tip.style.color = '#fff';
    tip.style.padding = '2px 4px';
    tip.style.borderRadius = '3px';
    tip.style.fontSize = '12px';
    document.body.appendChild(tip);
  }
  tip.style.left = `${x}px`;
  tip.style.top = `${y}px`;
  tip.textContent = text;
  tip.style.display = 'block';
}

export function hideTooltip() {
  const tip = document.getElementById('tooltip');
  if (tip) {
    tip.style.display = 'none';
  }
}
