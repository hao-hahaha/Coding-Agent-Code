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
    <label>Pop <input id="sim-pop" type="number" min="1" value="50"></label>
    <label>Gen <input id="sim-gen" type="number" min="1" value="10"></label>
    <button id="sim-start">Start</button>
    <button id="sim-cancel">Cancel</button>
    <progress id="sim-progress" value="0" max="1" style="width:100%"></progress>
  `;
  document.body.appendChild(panel);

  const popInput = panel.querySelector('#sim-pop');
  const genInput = panel.querySelector('#sim-gen');
  const startBtn = panel.querySelector('#sim-start');
  const cancelBtn = panel.querySelector('#sim-cancel');
  const progress = panel.querySelector('#sim-progress');

  let sim = null;

  startBtn.addEventListener('click', async () => {
    if (sim) sim.cancel();
    sim = new Simulator({
      popSize: Number(popInput.value),
      generations: Number(genInput.value),
      workerUrl: './worker/evolver.js',
    });
    let lastPop = [];
    let count = 0;
    for await (const g of sim.run()) {
      lastPop = g.pop;
      count = g.gen;
      progress.value = count / sim.opts.generations;
      const front = paretoFront(g.pop);
      await archive.add(sim.opts.seed ?? 1, { popSize: sim.opts.popSize }, front).catch(() => {});
    }
    if (!sim.cancelled) {
      const json = save(lastPop, 0);
      const file = new File([json], 'replay.json', { type: 'application/json' });
      await pinFiles([file]);
    }
  });

  cancelBtn.addEventListener('click', () => {
    if (sim) sim.cancel();
  });

  return panel;
}
