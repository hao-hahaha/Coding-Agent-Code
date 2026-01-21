// SPDX-License-Identifier: Apache-2.0
export function initDragDrop(el, onDrop) {
  function over(ev) {
    ev.preventDefault();
    el.classList.add('drag');
  }
  function leave() {
    el.classList.remove('drag');
  }
  function drop(ev) {
    ev.preventDefault();
    el.classList.remove('drag');
    const file = ev.dataTransfer.files && ev.dataTransfer.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => onDrop(reader.result);
    reader.readAsText(file);
  }
  el.addEventListener('dragover', over);
  el.addEventListener('dragleave', leave);
  el.addEventListener('drop', drop);
}
