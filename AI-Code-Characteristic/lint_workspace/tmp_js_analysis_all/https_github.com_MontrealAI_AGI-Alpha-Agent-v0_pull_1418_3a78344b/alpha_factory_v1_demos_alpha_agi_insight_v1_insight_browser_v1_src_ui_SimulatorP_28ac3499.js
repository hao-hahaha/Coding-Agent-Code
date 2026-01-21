// SPDX-License-Identifier: Apache-2.0
import { Simulator } from '../simulator.ts';
import { save, load } from '../state/serializer.js';
import { ReplayDB } from '@insight-src/replay.ts';
import { mineMemes, saveMemes } from '@insight-src/memeplex.ts';
import { mutateEvaluator } from '../evaluator_genome.ts';
import { pinFiles } from '../ipfs/pinner.js';
import { renderFrontier } from '../render/frontier.js';
import { detectColdZone } from '../utils/cluster.js';

export async function initSimulatorPanel(archive, power) {
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
    <button id="sim-pause">Pause</button>
    <button id="sim-fork">Fork</button>
    <button id="sim-cancel">Cancel</button>
    <progress id="sim-progress" value="0" max="1" class="w-full"></progress>
    <input id="sim-frame" type="range" min="0" value="0" step="1" class="w-full">
    <div id="sim-status"></div>
    <pre id="sim-inspect" class="max-h-[40vh] overflow-auto"></pre>
  `;
  document.body.appendChild(panel);

  const seedsInput = panel.querySelector('#sim-seeds');
  const popInput = panel.querySelector('#sim-pop');
  const genInput = panel.querySelector('#sim-gen');
  const rateInput = panel.querySelector('#sim-rate');
  const heurSel = panel.querySelector('#sim-heur');
  const startBtn = panel.querySelector('#sim-start');
  const pauseBtn = panel.querySelector('#sim-pause');
  const forkBtn = panel.querySelector('#sim-fork');
  const cancelBtn = panel.querySelector('#sim-cancel');
  const progress = panel.querySelector('#sim-progress');
  const frameInput = panel.querySelector('#sim-frame');
  const status = panel.querySelector('#sim-status');
  const inspectPre = panel.querySelector('#sim-inspect');

  let sim = null;
  let frames = [];
  let frameIds = [];
  let paused = false;
  const replay = new ReplayDB('sim-replay');
  await replay.open();
  let memeRuns = [];
  let evaluator = { weights: { logic: 0.5, feasible: 0.5 }, prompt: 'score idea' };

  function showFrame(i) {
    const f = frames[i];
    if (!f) return;
    pop = f;
    gen = i;
    window.pop = pop;
    renderFrontier(view.node ? view.node() : view, pop, selectPoint);
    info.textContent = `gen ${i}`;
    if (inspectPre) inspectPre.textContent = JSON.stringify(f, null, 2);
  }

  frameInput.addEventListener('input', () => {
    showFrame(Number(frameInput.value));
  });

  startBtn.addEventListener('click', async () => {
    if (sim && typeof sim.return === 'function') await sim.return();
    const seeds = seedsInput.value.split(',').map((s) => Number(s.trim())).filter(Boolean);
    memeRuns = [];
    sim = Simulator.run({
      popSize: Number(popInput.value),
      generations: Number(genInput.value),
      mutations: ['gaussian'],
      seeds,
      workerUrl: './worker/evolver.js',
      umapWorkerUrl: './worker/umapWorker.js',
      critic: heurSel.value,
    });
    let lastPop = [];
    let count = 0;
    frames = [];
    frameIds = [];
    paused = false;
    let evalId = await archive.addEvaluator(evaluator);
    for await (const g of sim) {
      while (paused) {
        await new Promise((r) => setTimeout(r, 100));
      }
      lastPop = g.population;
      const edges = g.population.map((p) => ({ from: p.strategy || 'x', to: p.strategy || 'x' }));
      memeRuns.push({ edges });
      await saveMemes(mineMemes(memeRuns));
      frames.push(structuredClone(g.population));
      const fid = await replay.addFrame(frameIds[frameIds.length - 1] || null, { population: g.population, gen: g.gen });
      frameIds.push(fid);
      count = g.gen;
      window.pop = g.population;
      if (g.population[0] && g.population[0].umap) {
        const pts = g.population.map((p) => p.umap);
        window.coldZone = detectColdZone(pts);
      }
      progress.value = count / Number(genInput.value);
      status.textContent = `gen ${count} front ${g.fronts.length}`;
      await archive
        .add(seeds[0] ?? 1, { popSize: Number(popInput.value) }, g.fronts, [], evalId)
        .catch(() => {});
      power.update(evaluator);
      evaluator = mutateEvaluator(evaluator);
      evalId = await archive.addEvaluator(evaluator);
    }
    frameInput.max = Math.max(0, frames.length - 1);
    frameInput.value = String(frames.length - 1);
    showFrame(frames.length - 1);
    const share = await replay.share(frameIds[frameIds.length - 1]);
    const file = new File([share.data], 'replay.json', { type: 'application/json' });
    const out = await pinFiles([file]);
    if (out) status.textContent = `CID: ${share.cid}`;
  });

  cancelBtn.addEventListener('click', () => {
    if (sim && typeof sim.return === 'function') sim.return();
  });

  pauseBtn.addEventListener('click', () => {
    paused = !paused;
    pauseBtn.textContent = paused ? 'Resume' : 'Pause';
  });

  forkBtn.addEventListener('click', async () => {
    const idx = Number(frameInput.value);
    const fid = frameIds[idx];
    if (!fid) return;
    const share = await replay.share(fid);
    window.open(`#cid=${share.cid}`, '_blank');
  });

  const q = new URLSearchParams(window.location.hash.replace(/^#\/?/, ''));
  const cid = q.get('cid');
  if (cid) {
    const gateway = (window.IPFS_GATEWAY || 'https://ipfs.io/ipfs').replace(/\/$/, '');
    fetch(`${gateway}/${cid}`)
      .then((r) => r.text())
      .then(async (txt) => {
        status.textContent = 'replaying...';
        frames = [];
        frameIds = [];
        try {
          const last = await replay.importFrames(txt);
          const thread = await replay.exportThread(last);
          frames = thread.map((f) => f.delta.population);
          frameIds = thread.map((f) => f.id);
          frameInput.max = String(Math.max(0, frames.length - 1));
          frameInput.value = '0';
          showFrame(0);
        } catch {
          /* ignore */
        }
      })
      .catch(() => {});
  }

  return panel;
}
