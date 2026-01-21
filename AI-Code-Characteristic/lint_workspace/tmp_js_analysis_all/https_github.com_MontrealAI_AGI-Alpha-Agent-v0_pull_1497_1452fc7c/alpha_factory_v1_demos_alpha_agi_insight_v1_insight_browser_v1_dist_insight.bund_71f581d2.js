(function(){
const style='/* SPDX-License-Identifier: Apache-2.0 */\n:root {\n  --color-bg: #111;\n  --color-bg-alt: #181818;\n  --color-text: #eee;\n  --color-border: #333;\n  --size-xs: 2px;\n  --size-s: 4px;\n  --size-m: 10px;\n  --size-l: 12px;\n}\n\n[data-theme="light"] {\n  --color-bg: #fff;\n  --color-bg-alt: #fafafa;\n  --color-text: #000;\n  --color-border: #ccc;\n}\n\n@media (prefers-color-scheme: light) {\n  :root:not([data-theme]) {\n    --color-bg: #fff;\n    --color-bg-alt: #fafafa;\n    --color-text: #000;\n    --color-border: #ccc;\n  }\n}\nbody{margin:0;font-family:Inter,Helvetica,Arial,sans-serif;background:#111;color:#eee}\nsvg{display:block;margin:auto;background:#181818;border:1px solid #333;touch-action:none}\n@media(prefers-color-scheme:light){\n  body{background:#fff;color:#000}\n  svg{background:#fafafa;border-color:#ccc}\n  #legend{color:#000}\n}\n#legend{color:#eee}\n:root[data-theme="light"] body{background:#fff;color:#000}\n:root[data-theme="light"] svg{background:#fafafa;border-color:#ccc}\n:root[data-theme="light"] #legend{color:#000}\n#tooltip{position:absolute;display:none;pointer-events:none;background:rgba(0,0,0,0.7);color:#fff;padding:2px 4px;border-radius:3px;font-size:12px}\n#toolbar{position:fixed;bottom:10px;left:10px}\n#toolbar button{margin-right:4px}\n#legend{position:fixed;bottom:10px;right:10px;font-size:12px}\n#legend span{margin-left:6px}\n/* SPDX-License-Identifier: Apache-2.0 */\n#controls{position:fixed;top:10px;right:10px;background:rgba(0,0,0,.7);padding:8px;color:#fff;font:14px sans-serif}\n#controls label{display:block;margin-bottom:4px}\n#controls button{margin-right:4px;margin-top:4px}\n#controls input:focus,#controls button:focus,#drop:focus{outline:2px solid #ff0;outline-offset:2px}\n#drop{margin-top:4px;padding:10px;border:1px dashed #888;text-align:center;font-size:12px}\n#drop.drag{background:rgba(255,255,255,.1)}\n#toast{position:fixed;bottom:10px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,.8);color:#fff;padding:4px 8px;opacity:0;transition:opacity .3s}\n#toast.show{opacity:1}\n@media(prefers-color-scheme:light){#controls{background:rgba(255,255,255,.9);color:#000}#toast{background:rgba(238,238,238,.9);color:#000}#drop{border-color:#aaa}#drop.drag{background:rgba(0,0,0,.05)}}\n:root[data-theme="light"] #controls{background:rgba(255,255,255,.9);color:#000}\n:root[data-theme="light"] #toast{background:rgba(238,238,238,.9);color:#000}\n:root[data-theme="light"] #drop{border-color:#aaa}\n:root[data-theme="light"] #drop.drag{background:rgba(0,0,0,.05)}\n';
const s=document.createElement('style');s.textContent=style;document.head.appendChild(s);
const EVOLVER_URL=URL.createObjectURL(new Blob(["// SPDX-License-Identifier: Apache-2.0\nimport { mutate } from '../src/evolve/mutate.js';\nimport { paretoFront } from '../src/utils/pareto.js';\nimport { lcg } from '../src/utils/rng.js';\n\nconst ua = self.navigator?.userAgent ?? '';\nconst isSafari = /Safari/.test(ua) && !/Chrome|Chromium|Edge/.test(ua);\nconst isIOS = /(iPad|iPhone|iPod)/.test(ua);\nlet pyReady;\nlet warned = false;\nlet pySupported = !(isSafari || isIOS);\n\nasync function loadPy() {\n  if (!pySupported) {\n    if (!warned) {\n      self.postMessage({ toast: 'Pyodide unavailable; using JS only' });\n      warned = true;\n    }\n    return null;\n  }\n  if (!pyReady) {\n    try {\n      const mod = await import('../src/wasm/bridge.js');\n      pyReady = mod.initPy ? mod.initPy() : null;\n    } catch {\n      pyReady = null;\n      pySupported = false;\n      if (!warned) {\n        self.postMessage({ toast: 'Pyodide failed to load; using JS only' });\n        warned = true;\n      }\n    }\n  }\n  return pyReady;\n}\n\nfunction shuffle(arr, rand) {\n  for (let i = arr.length - 1; i > 0; i--) {\n    const j = Math.floor(rand() * (i + 1));\n    [arr[i], arr[j]] = [arr[j], arr[i]];\n  }\n}\n\nself.onmessage = async (ev) => {\n  const { pop, rngState, mutations, popSize, critic, gen, adaptive, sigmaScale = 1 } = ev.data;\n  const rand = lcg(0);\n  rand.set(rngState);\n  let next = mutate(pop, rand, mutations, gen, adaptive, sigmaScale);\n  const front = paretoFront(next);\n  next.forEach((d) => (d.front = front.includes(d)));\n  if (critic === 'llm') {\n    await loadPy();\n  }\n  shuffle(next, rand);\n  next = front.concat(next.slice(0, popSize - 10));\n  const metrics = {\n    avgLogic: next.reduce((s, d) => s + (d.logic ?? 0), 0) / next.length,\n    avgFeasible: next.reduce((s, d) => s + (d.feasible ?? 0), 0) / next.length,\n    frontSize: front.length,\n  };\n  self.postMessage({ pop: next, rngState: rand.state(), front, metrics });\n};\n"],{type:'text/javascript'}));
const ARENA_URL=URL.createObjectURL(new Blob(["// SPDX-License-Identifier: Apache-2.0\n/*\n * Simple debate arena executed in a Web Worker. The worker receives a\n * hypothesis string and runs a fixed exchange between four roles:\n * Proposer, Skeptic, Regulator and Investor. The outcome score is\n * returned to the caller along with the threaded messages.\n */\nself.onmessage = (ev) => {\n  const { hypothesis } = ev.data || {};\n  if (!hypothesis) return;\n\n  const messages = [\n    { role: 'Proposer', text: `I propose that ${hypothesis}.` },\n    { role: 'Skeptic', text: `I doubt that ${hypothesis} holds under scrutiny.` },\n    { role: 'Regulator', text: `Any implementation of ${hypothesis} must be safe.` },\n  ];\n\n  const approved = Math.random() > 0.5;\n  messages.push({\n    role: 'Investor',\n    text: approved\n      ? `Funding approved for: ${hypothesis}.`\n      : `Funding denied for: ${hypothesis}.`,\n  });\n\n  const score = approved ? 1 : 0;\n  self.postMessage({ messages, score });\n};\n"],{type:'text/javascript'}));
(function() {
/* Placeholder for web3.storage bundle.esm.min.js
   The actual file should be downloaded from:
   https://cdn.jsdelivr.net/npm/web3.storage/dist/bundle.esm.min.js
*/
function clonePolyfill(o){if(o===null||typeof o!=='object')return o;if(o instanceof Date)return new Date(o.getTime());if(Array.isArray(o))return o.map(i=>clonePolyfill(i));const r={};for(const k of Object.keys(o))r[k]=clonePolyfill(o[k]);return r;}const clone=globalThis.structuredClone?((v)=>globalThis.structuredClone(v)):clonePolyfill;
function Web3Storage(){ throw new Error('web3.storage not bundled'); }

// SPDX-License-Identifier: Apache-2.0
const defaults={seed:42,pop:80,gen:60,mutations:['gaussian']};
function parseHash(h=window.location.hash){
  if(!h || h==='#'){
    try{
      const stored=localStorage.getItem('insightParams');
      if(stored){
        const p=JSON.parse(stored);
        return{
          seed:p.seed??defaults.seed,
          pop:p.pop??defaults.pop,
          gen:p.gen??defaults.gen,
          mutations:p.mutations??defaults.mutations
        };
      }
    }catch{}
  }
  const q=new URLSearchParams(h.replace(/^#\/?/,''));
  return{
    seed:+q.get('s')||defaults.seed,
    pop:+q.get('p')||defaults.pop,
    gen:+q.get('g')||defaults.gen,
    mutations:(q.get('m')||defaults.mutations.join(',')).split(',').filter(Boolean)
  };
}
function toHash(p){
  const q=new URLSearchParams();
  q.set('s',p.seed);q.set('p',p.pop);q.set('g',p.gen);
  if(p.mutations) q.set('m',p.mutations.join(','));
  return'#/'+q.toString();
}

// SPDX-License-Identifier: Apache-2.0
let strings={};
let currentLanguage='en';
async function initI18n(){
  const saved=localStorage.getItem('lang');
  const lang=(saved||navigator.language||'en').slice(0,2);
  currentLanguage=lang.startsWith('fr')?'fr':'en';
  const res=await fetch(`src/i18n/${currentLanguage}.json`);
  strings=await res.json();
}
async function setLanguage(lang){
  currentLanguage=lang;
  localStorage.setItem('lang',lang);
  const res=await fetch(`src/i18n/${lang}.json`);
  strings=await res.json();
}
function t(key){
  return strings[key]||key;
}

// SPDX-License-Identifier: Apache-2.0
const MAX_VAL=500;
function initControls(params,onChange){
  const root=document.getElementById('controls');
  root.innerHTML=`<label>${t('seed')} <input id="seed" type="number" min="0" aria-label="${t('seed')}" tabindex="1"></label>
<label>${t('population')} <input id="pop" type="number" min="1" max="${MAX_VAL}" aria-label="${t('population')}" tabindex="2"></label>
<label>${t('generations')} <input id="gen" type="number" min="1" max="${MAX_VAL}" aria-label="${t('generations')}" tabindex="3"></label>
<label><input id="gaussian" type="checkbox" aria-label="${t('gaussian')}" tabindex="4"> ${t('gaussian')}</label>
<label><input id="swap" type="checkbox" aria-label="${t('swap')}" tabindex="5"> ${t('swap')}</label>
<label><input id="jump" type="checkbox" aria-label="${t('jump')}" tabindex="6"> ${t('jump')}</label>
<label><input id="scramble" type="checkbox" aria-label="${t('scramble')}" tabindex="7"> ${t('scramble')}</label>
<button id="pause" role="button" aria-label="${t('pause')}" tabindex="8">${t('pause')}</button>
<button id="export" role="button" aria-label="${t('export')}" tabindex="9">${t('export')}</button>
<div id="drop" role="button" aria-label="${t('drop')}" tabindex="10">${t('drop')}</div>
<select id="lang" tabindex="11">
  <option value="en">English</option>
  <option value="fr">Français</option>
</select>`;
  const seed=root.querySelector('#seed'),
        pop=root.querySelector('#pop'),
        gen=root.querySelector('#gen'),
        gauss=root.querySelector('#gaussian'),
        swap=root.querySelector('#swap'),
        jump=root.querySelector('#jump'),
        scramble=root.querySelector('#scramble');
  function update(p){
    seed.value=p.seed;
    pop.value=Math.min(p.pop,MAX_VAL);
    gen.value=Math.min(p.gen,MAX_VAL);
    const set=new Set(p.mutations||[]);
    gauss.checked=set.has('gaussian');
    swap.checked=set.has('swap');
    jump.checked=set.has('jump');
    scramble.checked=set.has('scramble');
  }
  update(params);
  function emit(){
    const muts=[gauss,swap,jump,scramble].filter(c=>c.checked).map(c=>c.id);
    let popVal=Math.min(+pop.value,MAX_VAL);
    let genVal=Math.min(+gen.value,MAX_VAL);
    const info={popClamped:popVal!==+pop.value,genClamped:genVal!==+gen.value};
    pop.value=popVal;
    gen.value=genVal;
    const p={seed:+seed.value,pop:popVal,gen:genVal,mutations:muts};
    try{localStorage.setItem('insightParams',JSON.stringify(p));}catch{}
    onChange(p,info);
  }
  seed.addEventListener('change',emit);
  pop.addEventListener('change',emit);
  gen.addEventListener('change',emit);
  gauss.addEventListener('change',emit);
  swap.addEventListener('change',emit);
  jump.addEventListener('change',emit);
  scramble.addEventListener('change',emit);
  const pause=root.querySelector('#pause'),
        exportBtn=root.querySelector('#export'),
        drop=root.querySelector('#drop'),
        langSel=root.querySelector('#lang');
  langSel.value=currentLanguage;
  langSel.addEventListener('change',async()=>{await setLanguage(langSel.value);location.reload();});
  return{setValues:update,pauseBtn:pause,exportBtn,dropZone:drop};
}

// SPDX-License-Identifier: Apache-2.0
function paretoFront(pop) {
  if (pop.length === 0) return [];

  // Sort by logic (desc) then feasible (desc) and scan once.
  const sorted = [...pop].sort(
    (a, b) => b.logic - a.logic || b.feasible - a.feasible,
  );

  const front = [];
  let bestFeasible = -Infinity;
  for (const p of sorted) {
    if (p.feasible >= bestFeasible) {
      front.push(p);
      bestFeasible = p.feasible;
    }
  }

  return front;
}

// SPDX-License-Identifier: Apache-2.0
const strategyColors = {
  gaussian: '#ff7f0e',
  swap: '#2ca02c',
  jump: '#d62728',
  scramble: '#9467bd',
  front: '#00afff',
  base: '#666',
};
function credibilityColor(v) {
  const clamped = Math.max(0, Math.min(1, v ?? 0));
  const hue = 120 * clamped; // red -> green
  return `hsl(${hue},70%,50%)`;
}
function depthColor(depth, maxDepth) {
  const md = Math.max(1, maxDepth ?? depth ?? 1);
  const ratio = 1 - Math.min(depth ?? 0, md) / md;
  return `rgba(0,175,255,${ratio})`;
}

// SPDX-License-Identifier: Apache-2.0
function renderFrontier(container, pop, onSelect) {
  const front = paretoFront(pop).sort((a, b) => a.logic - b.logic);

  const maxDepth = pop.reduce((m, d) => Math.max(m, d.depth ?? 0), 0);
  const dotOptions = {
    x: 'logic',
    y: 'feasible',
    r: 3,
    fill: (d) => depthColor(d.depth ?? 0, maxDepth),
    title: (d) => `${d.summary ?? ''}\n${d.critic ?? ''}`,
  };

  const marks = [
    Plot.areaY(front, {
      x: 'logic',
      y: 'feasible',
      fill: 'rgba(0,175,255,0.2)',
      stroke: null,
    }),
  ];

  marks.push(
    pop.length > 10000 ? plotCanvas(Plot.dot(pop, dotOptions)) : Plot.dot(pop, dotOptions),
  );

  const plot = Plot.plot({
    width: 500,
    height: 500,
    x: { domain: [0, 1] },
    y: { domain: [0, 1] },
    marks,
  });

  container.innerHTML = '';
  container.append(plot);
  if (onSelect) {
    d3.select(plot).selectAll('circle').on('click', function (_, d) {
      onSelect(d, this);
    });
  }
}

// SPDX-License-Identifier: Apache-2.0
function initCriticPanel() {
  const root = document.createElement('div');
  root.id = 'critic-panel';
  Object.assign(root.style, {
    position: 'fixed',
    top: '10px',
    right: '10px',
    background: 'rgba(0,0,0,0.7)',
    color: '#fff',
    padding: '8px',
    font: '14px sans-serif',
    display: 'none',
    zIndex: 1000,
  });

  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '200');
  svg.setAttribute('height', '200');
  svg.id = 'critic-chart';

  const table = document.createElement('table');
  table.id = 'critic-table';
  table.style.marginTop = '4px';
  table.style.fontSize = '12px';

  root.appendChild(svg);
  root.appendChild(table);
  document.body.appendChild(root);

  let highlighted = null;

  function drawSpider(scores) {
    const labels = Object.keys(scores);
    const values = Object.values(scores);
    const size = 200;
    const center = size / 2;
    const radius = center - 20;
    const step = (Math.PI * 2) / labels.length;
    svg.innerHTML = '';
    const pts = [];
    labels.forEach((label, i) => {
      const angle = i * step - Math.PI / 2;
      const r = radius * (values[i] ?? 0);
      const x = center + r * Math.cos(angle);
      const y = center + r * Math.sin(angle);
      pts.push(`${x},${y}`);
      const lx = center + radius * Math.cos(angle);
      const ly = center + radius * Math.sin(angle);
      const tx = center + (radius + 12) * Math.cos(angle);
      const ty = center + (radius + 12) * Math.sin(angle);
      const line = document.createElementNS('http://www.w3.org/2000/svg','line');
      line.setAttribute('x1', center);
      line.setAttribute('y1', center);
      line.setAttribute('x2', lx);
      line.setAttribute('y2', ly);
      line.setAttribute('stroke', '#ccc');
      svg.appendChild(line);
      const text = document.createElementNS('http://www.w3.org/2000/svg','text');
      text.setAttribute('x', tx);
      text.setAttribute('y', ty);
      text.setAttribute('font-size', '10');
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('dominant-baseline', 'middle');
      text.textContent = label;
      svg.appendChild(text);
    });
    const poly = document.createElementNS('http://www.w3.org/2000/svg','polygon');
    poly.setAttribute('points', pts.join(' '));
    poly.setAttribute('fill', 'rgba(0,100,250,0.3)');
    poly.setAttribute('stroke', 'blue');
    svg.appendChild(poly);
  }

  function show(scores, element) {
    if (highlighted) highlighted.removeAttribute('stroke');
    if (element) {
      element.setAttribute('stroke', 'yellow');
      highlighted = element;
    }
    drawSpider(scores);
    table.innerHTML = Object.entries(scores)
      .map(([k,v]) => `<tr><th>${k}</th><td>${v.toFixed(2)}</td></tr>`) 
      .join('');
    root.style.display = 'block';
  }

  return { show };
}

// SPDX-License-Identifier: Apache-2.0
async function loadExamples(url = '../data/critics/innovations.txt') {
  try {
    const res = await fetch(url);
    if (!res.ok) return [];
    const text = await res.text();
    return text.split(/\n/).map(l => l.trim()).filter(Boolean);
  } catch {
    return [];
  }
}
class LogicCritic {
  constructor(examples = [], prompt = 'judge logic') {
    this.examples = examples;
    this.prompt = prompt;
    this.index = {};
    this.examples.forEach((e, i) => {
      this.index[e.toLowerCase()] = i;
    });
    this.scale = Math.max(this.examples.length - 1, 1);
  }

  score(genome) {
    const key = String(genome).toLowerCase();
    const pos = this.index[key] ?? -1;
    const base = pos >= 0 ? (pos + 1) / (this.scale + 1) : 0;
    const noise = Math.random() * 0.001;
    const val = base + noise;
    return Math.min(1, Math.max(0, val));
  }
}
class FeasibilityCritic {
  constructor(examples = [], prompt = 'judge feasibility') {
    this.examples = examples;
    this.prompt = prompt;
  }

  static jaccard(a, b) {
    const sa = new Set(a);
    const sb = new Set(b);
    if (!sa.size || !sb.size) return 0;
    let inter = 0;
    for (const x of sa) if (sb.has(x)) inter++;
    const union = new Set([...a, ...b]).size;
    return inter / union;
  }

  score(genome) {
    const tokens = String(genome).toLowerCase().split(/\s+/);
    let best = 0;
    for (const ex of this.examples) {
      const sim = FeasibilityCritic.jaccard(tokens, ex.toLowerCase().split(/\s+/));
      if (sim > best) best = sim;
    }
    const noise = Math.random() * 0.001;
    const val = best + noise;
    return Math.min(1, Math.max(0, val));
  }
}

class JudgmentDB {
  constructor(name = 'critic-judgments') {
    this.store = createStore(name, 'judgments');
  }
  async add(genome, scores) {
    await set(Date.now() + Math.random(), { genome, scores }, this.store);
  }
  async querySimilar(genome) {
    const all = await values(this.store);
    const tokens = String(genome).toLowerCase().split(/\s+/);
    let best = null;
    let bestSim = -1;
    for (const rec of all) {
      const sim = FeasibilityCritic.jaccard(tokens, rec.genome.toLowerCase().split(/\s+/));
      if (sim > bestSim) {
        bestSim = sim;
        best = rec;
      }
    }
    return best;
  }
}

function mutatePrompt(prompt) {
  const words = ['insightful', 'detailed', 'robust', 'novel'];
  const tokens = prompt.split(/\s+/);
  if (Math.random() < 0.5 && tokens.length > 1) {
    tokens.splice(Math.floor(Math.random() * tokens.length), 1);
  } else {
    const w = words[Math.floor(Math.random() * words.length)];
    tokens.splice(Math.floor(Math.random() * (tokens.length + 1)), 0, w);
  }
  return tokens.join(' ');
}

function consilience(scores) {
  const vals = Object.values(scores);
  const avg = vals.reduce((s, v) => s + v, 0) / vals.length;
  const sd = Math.sqrt(vals.reduce((s, v) => s + (v - avg) ** 2, 0) / vals.length);
  return 1 - sd;
}

async function scoreGenome(genome, critics, db, threshold = 0.6) {
  const scores = {};
  for (const c of critics) {
    scores[c.constructor.name] = c.score(genome);
  }
  const past = db ? await db.querySimilar(genome) : null;
  if (past) {
    for (const k of Object.keys(scores)) {
      if (past.scores[k] !== undefined) {
        scores[k] = (scores[k] + past.scores[k]) / 2;
      }
    }
  }
  if (db) await db.add(genome, scores);
  const cons = consilience(scores);
  if (cons < threshold) {
    for (const c of critics) if (c.prompt) c.prompt = mutatePrompt(c.prompt);
    if (typeof window !== 'undefined') {
      window.recordedPrompts = critics.map((c) => c.prompt);
    }
  }
  return { scores, cons };
}

if (typeof window !== 'undefined') {
  window.JudgmentDB = JudgmentDB;
  window.consilience = consilience;
  window.scoreGenome = scoreGenome;
  window.LogicCritic = LogicCritic;
  window.FeasibilityCritic = FeasibilityCritic;
}

// SPDX-License-Identifier: Apache-2.0
function save(pop, rngState) {
  const data = {
    gen: pop.gen ?? 0,
    pop: Array.from(pop, (d) => ({
      logic: d.logic,
      feasible: d.feasible,
      front: d.front,
      strategy: d.strategy,
    })),
    rngState,
  };
  return JSON.stringify(data);
}
function load(json) {
  let data;
  try {
    data = JSON.parse(json);
  } catch (err) {
    throw new Error(`Malformed JSON: ${err.message}`);
  }

  if (data === null || typeof data !== 'object') {
    throw new Error('Invalid data');
  }

  const allowedRoot = new Set(['gen', 'pop', 'rngState']);
  for (const key of Object.keys(data)) {
    if (!allowedRoot.has(key)) {
      throw new Error(`Unexpected key: ${key}`);
    }
  }

  if (!Array.isArray(data.pop)) throw new Error('Invalid population');

  const allowedItem = new Set(['logic', 'feasible', 'front', 'strategy']);
  const pop = data.pop.map((d) => {
    if (d === null || typeof d !== 'object') {
      throw new Error('Invalid population item');
    }
    for (const key of Object.keys(d)) {
      if (!allowedItem.has(key)) {
        throw new Error(`Invalid key in population item: ${key}`);
      }
    }
    if (typeof d.logic !== 'number' || typeof d.feasible !== 'number') {
      throw new Error('Population items require numeric logic and feasible');
    }
    return {
      logic: d.logic,
      feasible: d.feasible,
      front: d.front,
      strategy: d.strategy,
    };
  });
  pop.gen = typeof data.gen === 'number' ? data.gen : 0;
  return { pop, rngState: data.rngState, gen: pop.gen };
}

// SPDX-License-Identifier: Apache-2.0
function initDragDrop(el, onDrop) {
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

// SPDX-License-Identifier: Apache-2.0
function toCSV(rows, headers) {
  if (!rows.length) return '';
  const keys = headers || Object.keys(rows[0]);
  const escape = (v) => `"${String(v).replace(/"/g, '""')}"`;
  const lines = [keys.join(',')];
  for (const row of rows) {
    lines.push(keys.map((k) => escape(row[k])).join(','));
  }
  return lines.join('\n');
}

// SPDX-License-Identifier: Apache-2.0
async function svg2png(svg) {
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

/* Placeholder for web3.storage bundle.esm.min.js
   The actual file should be downloaded from:
   https://cdn.jsdelivr.net/npm/web3.storage/dist/bundle.esm.min.js
*/
function Web3Storage(){ throw new Error('web3.storage not bundled'); }

/* SPDX-License-Identifier: Apache-2.0 */
async function pinFiles(files) {
  if (!window.PINNER_TOKEN) return null;
  try {
    const client = new Web3Storage({ token: window.PINNER_TOKEN });
    const cid = await client.put(files);
    const url = `https://ipfs.io/ipfs/${cid}`;
    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(url);
      } catch (_) {
        /* ignore */
      }
    }
    if (typeof window.toast === 'function') {
      window.toast(`pinned ${cid}`);
    }
    return { cid, url };
  } catch (err) {
    console.error('pinFiles failed', err);
    return null;
  }
}

// SPDX-License-Identifier: Apache-2.0
function initGestures(svg, view) {
  const state = { pointers: new Map(), lastDist: 0 };
  svg.addEventListener('pointerdown', (e) => {
    svg.setPointerCapture(e.pointerId);
    state.pointers.set(e.pointerId, [e.clientX, e.clientY]);
  });
  svg.addEventListener('pointermove', (e) => {
    if (!state.pointers.has(e.pointerId)) return;
    const prev = state.pointers.get(e.pointerId);
    const curr = [e.clientX, e.clientY];
    state.pointers.set(e.pointerId, curr);
    if (state.pointers.size === 1) {
      const dx = curr[0] - prev[0];
      const dy = curr[1] - prev[1];
      const t = view.transform.baseVal.consolidate();
      const m = t ? t.matrix : svg.createSVGMatrix();
      view.setAttribute('transform', m.translate(dx, dy).toString());
    } else if (state.pointers.size === 2) {
      const pts = Array.from(state.pointers.values());
      const dist = Math.hypot(pts[0][0]-pts[1][0], pts[0][1]-pts[1][1]);
      if (state.lastDist) {
        const scale = dist / state.lastDist;
        const t = view.transform.baseVal.consolidate();
        const m = t ? t.matrix : svg.createSVGMatrix();
        const cx = (pts[0][0]+pts[1][0]) / 2;
        const cy = (pts[0][1]+pts[1][1]) / 2;
        const matrix = m
          .translate(cx, cy)
          .scale(scale)
          .translate(-cx, -cy);
        view.setAttribute('transform', matrix.toString());
      }
      state.lastDist = dist;
    }
  });
  svg.addEventListener('pointerup', (e) => {
    state.pointers.delete(e.pointerId);
    if (state.pointers.size < 2) state.lastDist = 0;
  });
  svg.addEventListener('pointercancel', (e) => {
    state.pointers.delete(e.pointerId);
    if (state.pointers.size < 2) state.lastDist = 0;
  });
}

// SPDX-License-Identifier: Apache-2.0
function initFpsMeter(isRunning) {
  if (document.getElementById('fps-meter')) return;
  const el = document.createElement('div');
  el.id = 'fps-meter';
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

// SPDX-License-Identifier: Apache-2.0
let localModel;

async function loadLocal() {
  if (!localModel) {
    try {
      const { pipeline } = await import('../lib/bundle.esm.min.js');
      localModel = await pipeline('text-generation', './wasm_llm/');
    } catch (err) {
      localModel = async (p) => `[offline] ${p}`;
    }
  }
  return localModel;
}
async function chat(prompt) {
  const key = localStorage.getItem('OPENAI_API_KEY');
  if (key) {
    const resp = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: [{ role: 'user', content: prompt }],
      }),
    });
    const data = await resp.json();
    return data.choices[0].message.content.trim();
  }
  const model = await loadLocal();
  const out = await model(prompt);
  return typeof out === 'string' ? out : out[0]?.generated_text?.trim();
}


// SPDX-License-Identifier: Apache-2.0
/**
 * Lightweight telemetry helper.
 * Prompts for user consent and sends anonymous metrics to the OTLP endpoint.
 */
async function hashSession(id) {
  const buf = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode('insight' + id),
  );
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}
function initTelemetry() {
  const endpoint =
    (typeof process !== 'undefined' && process.env.OTEL_ENDPOINT) ||
    (typeof window !== 'undefined' && window.OTEL_ENDPOINT) ||
    (typeof import.meta !== 'undefined' && import.meta.env.VITE_OTEL_ENDPOINT);

  if (!endpoint) {
    return { recordRun() {}, recordShare() {} };
  }

  const consentKey = 'telemetryConsent';
  let consent = localStorage.getItem(consentKey);
  if (consent === null) {
    const allow = window.confirm('Allow anonymous telemetry?');
    consent = allow ? 'true' : 'false';
    localStorage.setItem(consentKey, consent);
  }

  const enabled = consent === 'true';
  const queueKey = 'telemetryQueue';
  const metrics = { ts: Date.now(), session: '', generations: 0, shares: 0 };
  const queue = JSON.parse(localStorage.getItem(queueKey) || '[]');

  const ready = (async () => {
    let sid = localStorage.getItem('telemetrySession');
    if (!sid) {
      sid = await hashSession(crypto.randomUUID());
      localStorage.setItem('telemetrySession', sid);
    }
    metrics.session = sid;
  })();

  async function sendQueue() {
    if (!enabled) return;
    await ready;
    while (queue.length && navigator.onLine) {
      const payload = queue[0];
      if (navigator.sendBeacon(endpoint, JSON.stringify(payload))) {
        queue.shift();
      } else {
        break;
      }
    }
    localStorage.setItem(queueKey, JSON.stringify(queue));
  }

  function flush() {
    if (!enabled) return;
    metrics.ts = Date.now();
    queue.push({ ...metrics });
    localStorage.setItem(queueKey, JSON.stringify(queue));
    void sendQueue();
  }
  window.addEventListener('beforeunload', flush);
  window.addEventListener('online', () => void sendQueue());
  void sendQueue();

  return {
    recordRun(n) {
      if (enabled) metrics.generations += n;
    },
    recordShare() {
      if (enabled) metrics.shares += 1;
    },
  };
}

// SPDX-License-Identifier: Apache-2.0
function lcg(seed) {
  function rand() {
    seed = Math.imul(1664525, seed) + 1013904223 >>> 0;
    return seed / 2 ** 32;
  }
  rand.state = () => seed;
  rand.set = (s) => { seed = s >>> 0; };
  return rand;
}

// SPDX-License-Identifier: Apache-2.0
function createStore(dbName, storeName) {
  const dbp = new Promise((resolve, reject) => {
    const req = indexedDB.open(dbName, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(storeName);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return { dbp, storeName };
}

async function withStore(type, store, fn) {
  const db = await store.dbp;
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store.storeName, type);
    const st = tx.objectStore(store.storeName);
    const req = fn(st);
    tx.oncomplete = () => resolve(req?.result);
    tx.onerror = () => reject(tx.error);
  });
}
function get(key, store) {
  return withStore('readonly', store, (s) => s.get(key));
}
function set(key, val, store) {
  return withStore('readwrite', store, (s) => s.put(val, key));
}
function del(key, store) {
  return withStore('readwrite', store, (s) => s.delete(key));
}
function keys(store) {
  return withStore('readonly', store, (s) => s.getAllKeys());
}
function values(store) {
  return withStore('readonly', store, (s) => s.getAll());
}

// SPDX-License-Identifier: Apache-2.0
interface InsightRun {
  id: number;
  seed: number;
  params: any;
  paretoFront: any[];
  parents: number[];
  score: number;
  novelty: number;
  timestamp: number;
}
class Archive {
  private store;
  constructor(private name = 'insight-archive') {
    this.store = createStore(this.name, 'runs');
  }

  async open(): Promise<void> {
    await this.store.dbp;
  }

  private _vector(front: any[]): [number, number] {
    if (!front.length) return [0, 0];
    const l = front.reduce((s, d) => s + (d.logic ?? 0), 0) / front.length;
    const f = front.reduce((s, d) => s + (d.feasible ?? 0), 0) / front.length;
    return [l, f];
  }

  private _dist(a: [number, number], b: [number, number]): number {
    return Math.hypot(a[0] - b[0], a[1] - b[1]);
  }

  private async _novelty(vec: [number, number], k = 5): Promise<number> {
    const runs = await this.list();
    if (!runs.length) return 0;
    const dists = runs.map((r) => this._dist(vec, this._vector(r.paretoFront)));
    dists.sort((a, b) => a - b);
    const n = Math.min(k, dists.length);
    return dists.slice(0, n).reduce((s, d) => s + d, 0) / n;
  }

  async add(seed: number, params: any, paretoFront: any[], parents: number[] = []): Promise<number> {
    await this.open();
    const vec = this._vector(paretoFront);
    const score = (vec[0] + vec[1]) / 2;
    const novelty = await this._novelty(vec);
    const id = Date.now();
    const run: InsightRun = {
      id,
      seed,
      params,
      paretoFront,
      parents,
      score,
      novelty,
      timestamp: Date.now(),
    };
    try {
      await set(id, run, this.store);
    } catch (err) {
      if ((err == null ? void 0 : err.name) === "QuotaExceededError") {
        await this.prune();
        if (typeof window.toast === "function") {
          window.toast("Archive full; oldest runs pruned");
        }
        await set(id, run, this.store);
      } else {
        throw err;
      }
    }
    await this.prune(500);
    return id;
  }

  async list(): Promise<InsightRun[]> {
    await this.open();
    const runs = (await values(this.store)) as InsightRun[];
    runs.sort((a, b) => a.timestamp - b.timestamp);
    return runs;
  }

  async prune(max = 500): Promise<void> {
    const runs = await this.list();
    if (runs.length <= max) return;
    runs.sort((a, b) => a.score + a.novelty - (b.score + b.novelty));
    const remove = runs.slice(0, runs.length - max);
    await Promise.all(remove.map((r) => del(r.id, this.store)));
  }

  async selectParents(count: number, beta = 1, gamma = 1): Promise<InsightRun[]> {
    const runs = await this.list();
    if (!runs.length) return [];
    const scoreW = runs.map((r) => Math.exp(beta * r.score));
    const novW = runs.map((r) => Math.exp(gamma * r.novelty));
    const sumS = scoreW.reduce((a, b) => a + b, 0);
    const sumN = novW.reduce((a, b) => a + b, 0);
    const weights = runs.map((_, i) => (scoreW[i] / sumS) * (novW[i] / sumN));
    const selected: InsightRun[] = [];
    for (let i = 0; i < Math.min(count, runs.length); i++) {
      let r = Math.random();
      let idx = 0;
      for (; idx < weights.length; idx++) {
        if (r < weights[idx]) break;
        r -= weights[idx];
      }
      selected.push(runs[idx]);
    }
    return selected;
  }
}

// SPDX-License-Identifier: Apache-2.0
function initEvolutionPanel(archive) {
  const panel = document.createElement('div');
  panel.id = 'evolution-panel';
  Object.assign(panel.style, {
    position: 'fixed',
    bottom: '10px',
    left: '10px',
    background: 'rgba(0,0,0,0.7)',
    color: '#fff',
    padding: '8px',
    fontSize: '12px',
    zIndex: 1000,
    maxHeight: '40vh',
    overflowY: 'auto',
  });
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '200');
  svg.setAttribute('height', '100');
  const table = document.createElement('table');
  const header = document.createElement('tr');
  header.innerHTML =
    '<th data-k="seed">Seed</th><th data-k="score">Score</th><th data-k="novelty">Novelty</th><th data-k="timestamp">Time</th><th></th>';
  table.appendChild(header);
  panel.appendChild(svg);
  panel.appendChild(table);
  document.body.appendChild(panel);

  let sortKey = 'timestamp';
  let desc = true;
  header.querySelectorAll('th[data-k]').forEach((th) => {
    th.style.cursor = 'pointer';
    th.onclick = () => {
      const k = th.dataset.k;
      if (sortKey === k) desc = !desc;
      else {
        sortKey = k;
        desc = true;
      }
      render();
    };
  });

  function respawn(seed) {
    const q = new URLSearchParams(window.location.hash.replace(/^#\/?/, ''));
    q.set('s', seed);
    window.location.hash = '#/' + q.toString();
  }

  function drawTree(runs) {
    svg.innerHTML = '';
    const pos = new Map();
    runs.forEach((r, i) => {
      const x = 20 + i * 20;
      const y = 20;
      pos.set(r.id, { x, y });
      const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      c.setAttribute('cx', String(x));
      c.setAttribute('cy', String(y));
      c.setAttribute('r', '4');
      c.setAttribute('fill', 'white');
      svg.appendChild(c);
    });
    runs.forEach((r) => {
      const child = pos.get(r.id);
      if (!child) return;
      for (const p of r.parents || []) {
        const parent = pos.get(p);
        if (!parent) continue;
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', String(parent.x));
        line.setAttribute('y1', String(parent.y));
        line.setAttribute('x2', String(child.x));
        line.setAttribute('y2', String(child.y));
        line.setAttribute('stroke', 'white');
        svg.appendChild(line);
      }
    });
  }

  async function render() {
    const runs = await archive.list();
    runs.sort((a, b) => (desc ? b[sortKey] - a[sortKey] : a[sortKey] - b[sortKey]));
    table.querySelectorAll('tr').forEach((tr, i) => { if (i) tr.remove(); });
    runs.forEach((r) => {
      const tr = document.createElement('tr');
      const time = new Date(r.timestamp).toLocaleTimeString();
      tr.innerHTML = `<td>${r.seed}</td><td>${r.score.toFixed(2)}</td><td>${r.novelty.toFixed(2)}</td><td>${time}</td>`;
      const td = document.createElement('td');
      const btn = document.createElement('button');
      btn.textContent = 'Re-spawn';
      btn.onclick = () => respawn(r.seed);
      td.appendChild(btn);
      tr.appendChild(td);
      table.appendChild(tr);
    });
    drawTree(runs);
  }

  return { render };
}

// SPDX-License-Identifier: Apache-2.0
function mutate(pop, rand, strategies, gen = 0) {
  const clamp = (v) => Math.min(1, Math.max(0, v));
  const mutants = [];
  for (const d of pop) {
    for (const s of strategies) {
      switch (s) {
        case 'gaussian':
          mutants.push({
            logic: clamp(d.logic + (rand() - 0.5) * 0.12),
            feasible: clamp(d.feasible + (rand() - 0.5) * 0.12),
            strategy: s,
            depth: gen,
          });
          break;
        case 'swap': {
          const other = pop[Math.floor(rand() * pop.length)];
          mutants.push({ logic: other.logic, feasible: d.feasible, strategy: s, depth: gen });
          break;
        }
        case 'jump':
          mutants.push({ logic: rand(), feasible: rand(), strategy: s, depth: gen });
          break;
        case 'scramble': {
          const other = pop[Math.floor(rand() * pop.length)];
          mutants.push({ logic: d.logic, feasible: other.feasible, strategy: s, depth: gen });
          break;
        }
      }
    }
  }
  return pop.concat(mutants);
}

// SPDX-License-Identifier: Apache-2.0
interface SimulatorConfig {
  popSize: number;
  generations: number;
  mutations?: string[];
  seeds?: number[];
  workerUrl?: string;
  critic?: 'llm' | 'none';
}
interface Generation {
  gen: number;
  population: any[];
  fronts: any[];
  metrics: { avgLogic: number; avgFeasible: number; frontSize: number };
}
class Simulator {
  static async *run(opts: SimulatorConfig): AsyncGenerator<Generation> {
    const options = { mutations: ['gaussian'], seeds: [1], critic: 'none', ...opts };
    const rand = lcg(options.seeds![0]);
    let worker: Worker | null = null;
    let pop = Array.from({ length: options.popSize }, () => ({
      logic: rand(),
      feasible: rand(),
      strategy: 'base',
      depth: 0,
    }));
    for (let gen = 0; gen < options.generations; gen++) {
      let front: any[] = [];
      let metrics = { avgLogic: 0, avgFeasible: 0, frontSize: 0 };
      if (options.workerUrl && typeof Worker !== 'undefined') {
        if (!worker) worker = new Worker(options.workerUrl, { type: 'module' });
        const result: any = await new Promise((resolve) => {
          if (!worker) return resolve({ pop, rngState: rand.state(), front: [], metrics });
          worker.onmessage = (ev) => resolve(ev.data);
          worker.postMessage({
            pop,
            rngState: rand.state(),
            mutations: options.mutations,
            popSize: options.popSize,
            critic: options.critic,
            gen: gen + 1,
          });
        });
        pop = result.pop;
        rand.set(result.rngState);
        front = result.front;
        metrics = result.metrics;
      } else {
        pop = mutate(pop, rand, options.mutations ?? ['gaussian'], gen + 1);
        front = paretoFront(pop);
        pop.forEach((d) => (d.front = front.includes(d)));
        pop = front.concat(pop.slice(0, options.popSize - 10));
        metrics = {
          avgLogic: pop.reduce((s, d) => s + (d.logic ?? 0), 0) / pop.length,
          avgFeasible: pop.reduce((s, d) => s + (d.feasible ?? 0), 0) / pop.length,
          frontSize: front.length,
        };
      }
      yield { gen: gen + 1, population: pop, fronts: front, metrics };
    }
    if (worker) worker.terminate();
  }
}

// SPDX-License-Identifier: Apache-2.0
function initSimulatorPanel(archive) {
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
    <input id="sim-frame" type="range" min="0" value="0" step="1" style="width:100%">
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
  const frameInput = panel.querySelector('#sim-frame');
  const status = panel.querySelector('#sim-status');

  let sim = null;
  let frames = [];

  function showFrame(i) {
    const f = frames[i];
    if (!f) return;
    pop = f;
    gen = i;
    renderFrontier(view.node ? view.node() : view, pop, selectPoint);
    info.textContent = `gen ${i}`;
  }

  frameInput.addEventListener('input', () => {
    showFrame(Number(frameInput.value));
  });

  startBtn.addEventListener('click', async () => {
    if (sim && typeof sim.return === 'function') await sim.return();
    const seeds = seedsInput.value.split(',').map((s) => Number(s.trim())).filter(Boolean);
    sim = Simulator.run({
      popSize: Number(popInput.value),
      generations: Number(genInput.value),
      mutations: ['gaussian'],
      seeds,
      workerUrl: EVOLVER_URL,
      critic: heurSel.value,
    });
    let lastPop = [];
    let count = 0;
    frames = [];
    for await (const g of sim) {
      lastPop = g.population;
      frames.push(clone(g.population));
      count = g.gen;
      progress.value = count / Number(genInput.value);
      status.textContent = `gen ${count} front ${g.fronts.length}`;
      await archive.add(seeds[0] ?? 1, { popSize: Number(popInput.value) }, g.fronts).catch(() => {});
    }
    frameInput.max = Math.max(0, frames.length - 1);
    frameInput.value = String(frames.length - 1);
    showFrame(frames.length - 1);
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
        frames = [];
        try {
          const s = load(txt);
          frames.push(clone(s.pop));
          frameInput.max = '0';
          frameInput.value = '0';
          loadState(txt);
        } catch {
          /* ignore */
        }
      })
      .catch(() => {});
  }

  return panel;
}

function initArenaPanel(onDebate){
  const root=document.createElement('details');
  root.id='arena-panel';
  Object.assign(root.style,{position:'fixed',bottom:'10px',right:'220px',background:'rgba(0,0,0,0.7)',color:'#fff',padding:'8px',fontSize:'12px',zIndex:1000,maxHeight:'40vh',overflowY:'auto'});
  const summary=document.createElement('summary');
  summary.textContent='Debate Arena';
  const ranking=document.createElement('ul');
  ranking.id='ranking';
  const panel=document.createElement('div');
  panel.id='debate-panel';
  const msgs=document.createElement('ul');
  panel.appendChild(msgs);
  root.appendChild(summary);
  root.appendChild(ranking);
  root.appendChild(panel);
  document.body.appendChild(root);
  function render(front){
    ranking.innerHTML='';
    const sorted=[...front].sort((a,b)=>(b.rank||0)-(a.rank||0));
    sorted.forEach(p=>{const li=document.createElement('li');li.textContent=`Rank ${(p.rank||0).toFixed(1)} `;const btn=document.createElement('button');btn.textContent='Debate';btn.addEventListener('click',()=>onDebate&&onDebate(p));li.appendChild(btn);ranking.appendChild(li);});
  }
  function show(messages,score){
    msgs.innerHTML=messages.map(m=>`<li><strong>${m.role}:</strong> ${m.text}</li>`).join('');
    const li=document.createElement('li');li.textContent=`Score: ${score}`;msgs.appendChild(li);root.open=true;
  }
  return{render,show};
}


let panel,pauseBtn,exportBtn,dropZone
let criticPanel,logicCritic,feasCritic
let current,rand,pop,gen,svg,view,info,running=true
let worker
let telemetry
let fpsStarted=false;
let archive,evolutionPanel;
let arenaPanel,debateWorker,debateTarget;
function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast.id);
  toast.id = setTimeout(() => t.classList.remove('show'), 2000);
}
window.toast = toast;
window.llmChat=llmChat;

function applyTheme(t){
  document.documentElement.dataset.theme=t;
}
function loadTheme(){
  const saved=localStorage.getItem('theme');
  if(saved) applyTheme(saved);
  else if(window.matchMedia('(prefers-color-scheme:light)').matches) applyTheme('light');
}
function toggleTheme(){
  const cur=document.documentElement.dataset.theme==='light'?'light':'dark';
  const next=cur==='light'?'dark':'light';
  applyTheme(next);
  localStorage.setItem('theme',next);
}

function setupView(){
  d3.select('#canvas').select('svg').remove();
  svg=d3.select('#canvas').append('svg')
        .attr('viewBox','0 0 500 500')
        .style('touch-action','none');
  view=svg.append('g');
  info=svg.append('text').attr('x',20).attr('y',30).attr('fill','#fff')
  initGestures(svg.node(), view.node ? view.node() : view)
}

function updateLegend(strats){
  const legend=document.getElementById('legend');
  legend.innerHTML='';
  for(const s of strats){
    const span=document.createElement('span');
    const sw=document.createElement('i');
    sw.style.background=strategyColors[s];
    sw.style.display='inline-block';
    sw.style.width='10px';
    sw.style.height='10px';
    sw.style.marginRight='4px';
    span.appendChild(sw);
    span.append(s);
    legend.appendChild(span);
  }
}

function updateDepthLegend(max){
  const dl=document.getElementById('depth-legend');
  dl.innerHTML='depth';
  const bar=document.createElement('div');
  bar.className='bar';
  dl.appendChild(bar);
}

function start(p){
  current=p
  rand=lcg(p.seed)
  pop=Array.from({length:p.pop},()=>({logic:rand(),feasible:rand(),strategy:'base',depth:0}))
  gen=0
  running=true
  setupView()
  if(!fpsStarted){initFpsMeter(() => running);fpsStarted=true;}
  updateLegend(p.mutations)
  if(worker) worker.terminate()
  worker=new Worker(EVOLVER_URL,{type:'module'})
  worker.onmessage=ev=>{pop=ev.data.pop;rand.set(ev.data.rngState);requestAnimationFrame(step)}
  step()
}

function selectPoint(d, elem){
  const scores={
    logic:d.logic??0,
    feasible:d.feasible??0
  };
  if(logicCritic&&feasCritic){
    scores.logicCritic=logicCritic.score(`${d.logic}`);
    scores.feasCritic=feasCritic.score(`${d.feasible}`);
    scores.average=(scores.logicCritic+scores.feasCritic)/2;
  }
  if(criticPanel) criticPanel.show(scores,elem);
}

function step(){
  info.text(`gen ${gen}`)
  const front = paretoFront(pop)
  renderFrontier(view.node ? view.node() : view,pop,selectPoint)
  if(arenaPanel) arenaPanel.render(front)
  const md = Math.max(...pop.map(d=>d.depth||0))
  updateDepthLegend(md)
  archive.add(current.seed, current, front).then(()=>evolutionPanel.render()).catch(()=>{})
  if(!running)return
  if(gen++>=current.gen){worker.terminate();return}
  telemetry.recordRun(1)
  worker.postMessage({pop,rngState:rand.state(),mutations:current.mutations,popSize:current.pop,gen})
}

function togglePause(){
  running=!running
  pauseBtn.textContent=running?t('pause'):t('resume')
  if(running)requestAnimationFrame(step)
}

async function exportState(){
  pop.gen=gen
  const json=save(pop,rand.state())
  const blob=new Blob([json],{type:'application/json'})
  const a=document.createElement('a')
  a.href=URL.createObjectURL(blob)
  a.download='state.json'
  a.click()
  URL.revokeObjectURL(a.href)
  if(window.PINNER_TOKEN){
    const file=new File([json],'state.json',{type:'application/json'})
    await pinFiles([file])
  }
}

function exportCSV(data){
  const csv = toCSV(data);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], {type: "text/csv"}));
  a.download = "population.csv";
  a.click();
  URL.revokeObjectURL(a.href);
}

async function exportPNG(){
  if(!svg) return;
  const blob = await svg2png(svg.node ? svg.node() : svg.node());
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "frontier.png";
  a.click();
  URL.revokeObjectURL(a.href);
}

function loadState(text){
  try{
    const s=load(text)
    pop=s.pop
    gen=s.gen
    rand=lcg(0);rand.set(s.rngState)
    running=true
    pauseBtn.textContent=t('pause')
    setupView()
    updateLegend(current.mutations)
    if(worker) worker.terminate()
    worker=new Worker(EVOLVER_URL,{type:'module'})
    worker.onmessage=ev=>{pop=ev.data.pop;rand.set(ev.data.rngState);requestAnimationFrame(step)}
    step()
    toast(t('state_loaded'))
  }catch{toast(t('invalid_file'))}
}

function apply(p,info={}){if(info.popClamped)toast('max population is 500');if(info.genClamped)toast('max generations is 500');location.hash=toHash(p)}

window.addEventListener('DOMContentLoaded',async()=>{
  telemetry = initTelemetry();
  archive = new Archive();
  await archive.open();
  evolutionPanel = initEvolutionPanel(archive);
  initSimulatorPanel(archive);
  arenaPanel = initArenaPanel(pt => {debateTarget=pt;const hypo=pt.summary||`logic ${pt.logic}`;debateWorker.postMessage({hypothesis:hypo});});
  debateWorker = new Worker(ARENA_URL,{type:'module'});
  debateWorker.onmessage=ev=>{const {messages,score}=ev.data;if(debateTarget){debateTarget.rank=(debateTarget.rank||0)+score;pop.sort((a,b)=>(a.rank||0)-(b.rank||0));}arenaPanel.show(messages,score);arenaPanel.render(paretoFront(pop));};
  await evolutionPanel.render();
  window.archive = archive;
  await initI18n()
  loadTheme()
  const ex=await loadCriticExamples()
  logicCritic=new LogicCritic(ex)
  feasCritic=new FeasibilityCritic(ex)
  criticPanel=initCriticPanel()
  panel=initControls(parseHash(),apply)
  pauseBtn=panel.pauseBtn
  exportBtn=panel.exportBtn
  dropZone=panel.dropZone
  const tb=document.getElementById("toolbar");
  const csvBtn=document.createElement("button");
  csvBtn.textContent=t('csv');
  const pngBtn=document.createElement("button");
  pngBtn.textContent=t('png');
  const shareBtn=document.createElement("button");
  shareBtn.textContent=t('share');
  const themeBtn=document.createElement("button");
  themeBtn.textContent=t('theme');
  tb.appendChild(csvBtn);
  tb.appendChild(pngBtn);
  tb.appendChild(shareBtn);
  tb.appendChild(themeBtn);
  const installBtn=document.getElementById("install-btn");
  let deferredPrompt=null;
  window.addEventListener("beforeinstallprompt",e=>{e.preventDefault();deferredPrompt=e;installBtn.hidden=false;});
  installBtn.addEventListener("click",async()=>{if(!deferredPrompt)return;installBtn.hidden=true;deferredPrompt.prompt();try{await deferredPrompt.userChoice;}catch{}deferredPrompt=null;});
  window.addEventListener("appinstalled",()=>{installBtn.hidden=true;deferredPrompt=null;});
  csvBtn.addEventListener("click",()=>exportCSV(pop));
  pngBtn.addEventListener("click",exportPNG);
  shareBtn.addEventListener("click", async () => {
    telemetry.recordShare();
    const url = location.origin + location.pathname + location.hash;
    let pinned = null;
    if (window.PINNER_TOKEN) {
      const json = save(pop, rand.state());
      const file = new File([json], "state.json", { type: "application/json" });
      pinned = await pinFiles([file]);
    }
    if (pinned && pinned.url) {
      if (navigator.clipboard) {
        try { await navigator.clipboard.writeText(pinned.url); } catch {}
      }
      toast(`pinned ${pinned.cid}`);
    } else {
      if (navigator.clipboard) {
        try { await navigator.clipboard.writeText(url); } catch {}
      }
      toast(t('link_copied'));
    }
  });
  themeBtn.addEventListener("click",toggleTheme);
  pauseBtn.addEventListener('click',togglePause)
  exportBtn.addEventListener('click',exportState)
  initDragDrop(dropZone,loadState)
  window.dispatchEvent(new HashChangeEvent('hashchange'))
})
window.addEventListener('hashchange', () => {
  const p = parseHash();
  panel.setValues(p);
  start(p);
  toast(t('simulation_restarted'));
});

})();

})();
