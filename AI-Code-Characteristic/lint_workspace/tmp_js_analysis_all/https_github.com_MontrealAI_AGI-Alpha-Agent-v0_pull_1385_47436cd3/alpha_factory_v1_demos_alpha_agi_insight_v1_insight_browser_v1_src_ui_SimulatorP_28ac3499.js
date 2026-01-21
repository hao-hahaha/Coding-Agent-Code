// SPDX-License-Identifier: Apache-2.0
import { Simulator } from '../simulator.ts';
import { save } from '../state/serializer.js';
import { pinFiles } from '../ipfs/pinner.js';
import { paretoFront } from '../utils/pareto.js';

export function initSimulatorPanel(archive) {
  const panel = document.createElement('div');
  panel.id = 'simulator-panel';
  Object.assign(panel.style, {
    position: 'fixed',
    bottom: '10px',
    right: '10px',
    background: 'rgba(0,0,0,0.7)',
    color: '#fff',
    padding: '8px',
    fontSize: '12px',
    zIndex: 1000,
  });

  panel.innerHTML = `
    <label>Seeds <input id="sim-seeds" value="1"></label>
    <label>Pop <input id="sim-pop" type="number" min="1" value="50"></label>
    <label>Gen <input id="sim-gen" type="number" min="1" value="10"></label>
    <label>Rate <input id="sim-rate" type="number" step="0.01" value="1"></label>
    <label>Heuristic <select id="sim-heur"><option value="none">none</option><option value="llm">llm</option></select></label>
    <button id="sim-start">Start</button>
    <button id="sim-cancel">Cancel</button>
    <progress id="sim-progress" value="0" max="1" style="width:100%"></progress>
    <div id="sim-status"></div>
  `;
  document.body.appendChild(panel);

  const seedsInput = panel.querySelector('#sim-seeds');
  const popInput = panel.querySelector('#sim-pop');
  const genInput = panel.querySelector('#sim-gen');
  const rateInput = panel.querySelector('#sim-rate');
  const heurSel = panel.querySelector('#sim-heur');
  const startBtn = panel.querySelector('#sim-start');
  const cancelBtn = panel.querySelector('#sim-cancel');
  const progress = panel.querySelector('#sim-progress');
  const status = panel.querySelector('#sim-status');

  let sim = null;

  startBtn.addEventListener('click', async () => {
    if (sim && typeof sim.return === 'function') await sim.return();
    const seeds = seedsInput.value.split(',').map((s) => Number(s.trim())).filter(Boolean);
    sim = Simulator.run({
      popSize: Number(popInput.value),
      generations: Number(genInput.value),
      mutations: ['gaussian'],
      seeds,
      workerUrl: './worker/evolver.js',
      critic: heurSel.value,
    });
    let lastPop = [];
    let count = 0;
    for await (const g of sim) {
      lastPop = g.population;
      count = g.gen;
      progress.value = count / Number(genInput.value);
      status.textContent = `gen ${count} front ${g.fronts.length}`;
      await archive.add(seeds[0] ?? 1, { popSize: Number(popInput.value) }, g.fronts).catch(() => {});
    }
    const json = save(lastPop, 0);
    const file = new File([json], 'replay.json', { type: 'application/json' });
    const out = await pinFiles([file]);
    if (out) status.textContent = `CID: ${out.cid}`;
  });

  cancelBtn.addEventListener('click', () => {
    if (sim && typeof sim.return === 'function') sim.return();
  });

  const q = new URLSearchParams(window.location.hash.replace(/^#\/?/, ''));
  const cid = q.get('cid');
  if (cid) {
    fetch(`https://ipfs.io/ipfs/${cid}`)
      .then((r) => r.text())
      .then((txt) => {
        status.textContent = 'replaying...';
        const data = JSON.parse(txt);
        console.log('Replay', data);
      })
      .catch(() => {});
  }

  return panel;
}
