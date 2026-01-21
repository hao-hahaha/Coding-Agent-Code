// SPDX-License-Identifier: Apache-2.0

export function ensureLayer(parent) {
  const node = parent.node ? parent.node() : parent;
  let fo = node.querySelector('foreignObject#canvas-layer');
  if (!fo) {
    const svg = node.ownerSVGElement || node;
    const vb = svg.viewBox?.baseVal;
    const width = vb && vb.width ? vb.width : svg.clientWidth;
    const height = vb && vb.height ? vb.height : svg.clientHeight;
    fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
    fo.setAttribute('id', 'canvas-layer');
    fo.setAttribute('x', 0);
    fo.setAttribute('y', 0);
    fo.setAttribute('width', width);
    fo.setAttribute('height', height);
    fo.style.pointerEvents = 'none';
    fo.style.overflow = 'visible';
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    fo.appendChild(canvas);
    node.appendChild(fo);
    return canvas.getContext('2d');
  }
  const canvas = fo.querySelector('canvas');
  return canvas.getContext('2d');
}

export function drawPoints(parent, pop, x, y, colorFn) {
  const ctx = ensureLayer(parent);
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  const getColor = typeof colorFn === 'function' ? colorFn : () => colorFn;
  for (const d of pop) {
    ctx.fillStyle = getColor(d);
    ctx.beginPath();
    ctx.arc(x(d.logic), y(d.feasible), 3, 0, 2 * Math.PI);
    ctx.fill();
  }
  return ctx;
}
