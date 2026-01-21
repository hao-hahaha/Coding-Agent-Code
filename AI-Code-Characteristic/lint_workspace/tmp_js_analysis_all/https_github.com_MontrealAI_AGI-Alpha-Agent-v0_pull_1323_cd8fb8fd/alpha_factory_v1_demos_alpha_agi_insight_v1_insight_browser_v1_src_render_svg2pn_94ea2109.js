// SPDX-License-Identifier: Apache-2.0
export async function svg2png(svg) {
  const xml = new XMLSerializer().serializeToString(svg);
  const blob = new Blob([xml], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const img = new Image();
  const loaded = new Promise((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = reject;
    img.src = url;
  });
  await loaded;
  const canvas = document.createElement('canvas');
  const vb = svg.viewBox.baseVal;
  canvas.width = vb && vb.width ? vb.width : svg.clientWidth;
  canvas.height = vb && vb.height ? vb.height : svg.clientHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);
  URL.revokeObjectURL(url);
  return new Promise((resolve) => canvas.toBlob((b) => resolve(b), 'image/png'));
}
