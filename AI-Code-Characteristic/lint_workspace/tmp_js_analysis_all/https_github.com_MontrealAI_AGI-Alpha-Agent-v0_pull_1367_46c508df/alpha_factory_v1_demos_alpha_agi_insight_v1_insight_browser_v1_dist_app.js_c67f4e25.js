(function() {
/* Placeholder for web3.storage bundle.esm.min.js
   The actual file should be downloaded from:
   https://cdn.jsdelivr.net/npm/web3.storage/dist/bundle.esm.min.js
*/
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
function initControls(params,onChange){
  const root=document.getElementById('controls');
  root.innerHTML=`<label>${t('seed')} <input id="seed" type="number" min="0" aria-label="${t('seed')}" tabindex="1"></label>
<label>${t('population')} <input id="pop" type="number" min="1" aria-label="${t('population')}" tabindex="2"></label>
<label>${t('generations')} <input id="gen" type="number" min="1" aria-label="${t('generations')}" tabindex="3"></label>
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
    pop.value=p.pop;
    gen.value=p.gen;
    const set=new Set(p.mutations||[]);
    gauss.checked=set.has('gaussian');
    swap.checked=set.has('swap');
    jump.checked=set.has('jump');
    scramble.checked=set.has('scramble');
  }
  update(params);
  function emit(){
    const muts=[gauss,swap,jump,scramble].filter(c=>c.checked).map(c=>c.id);
    const p={seed:+seed.value,pop:+pop.value,gen:+gen.value,mutations:muts};
    try{localStorage.setItem('insightParams',JSON.stringify(p));}catch{}
    onChange(p);
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
function showTooltip(x, y, text) {
  let tip = document.getElementById('tooltip');
  if (!tip) {
    tip = document.createElement('div');
    tip.id = 'tooltip';
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
function hideTooltip() {
  const tip = document.getElementById('tooltip');
  if (tip) {
    tip.style.display = 'none';
  }
}

// SPDX-License-Identifier: Apache-2.0
function paretoFront(pop) {
  const front = [];
  for (const a of pop) {
    let dominated = false;
    for (const b of pop) {
      if (a === b) continue;
      if (
        b.logic >= a.logic &&
        b.feasible >= a.feasible &&
        (b.logic > a.logic || b.feasible > a.feasible)
      ) {
        dominated = true;
        break;
      }
    }
    if (!dominated) front.push(a);
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

function credibilityColor(v){
  const clamped=Math.max(0,Math.min(1,v??0));
  const hue=120*clamped;
  return`hsl(${hue},70%,50%)`;
}

// SPDX-License-Identifier: Apache-2.0
function ensureLayer(parent) {
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
function drawPoints(parent, pop, x, y, colorFn) {
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

// SPDX-License-Identifier: Apache-2.0
function addGlow(svg) {
  const defs = svg.append('defs');
  const filter = defs.append('filter').attr('id', 'glow');
  filter.append('feGaussianBlur').attr('stdDeviation', 2).attr('result', 'blur');
  const merge = filter.append('feMerge');
  merge.append('feMergeNode').attr('in', 'blur');
  merge.append('feMergeNode').attr('in', 'SourceGraphic');
}
function renderFrontier(container, pop) {
  const front = paretoFront(pop).sort((a, b) => a.logic - b.logic);
  const dotOpts = {x: 'logic', y: 'feasible', r: 3, fill: d => credibilityColor(d.insightCredibility ?? 0), title: d => `${d.summary ?? ''}\n${d.critic ?? ''}`};
  const marks = [Plot.areaY(front,{x:'logic',y:'feasible',fill:'rgba(0,175,255,0.2)',stroke:null})];
  marks.push(pop.length>1e4?plotCanvas(Plot.dot(pop,dotOpts)):Plot.dot(pop,dotOpts));
  const plot = Plot.plot({width:500,height:500,x:{domain:[0,1]},y:{domain:[0,1]},marks});
  container.innerHTML='';
  container.append(plot);
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
  const data = JSON.parse(json);
  if (!Array.isArray(data.pop)) throw new Error('Invalid population');
  const pop = data.pop.map((d) => ({
    logic: d.logic,
    feasible: d.feasible,
    front: d.front,
    strategy: d.strategy,
  }));
  pop.gen = data.gen ?? 0;
  return { pop, rngState: data.rngState, gen: data.gen ?? 0 };
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



function lcg(seed){
  function rand(){
    seed=Math.imul(1664525,seed)+1013904223>>>0;
    return seed/2**32;
  }
  rand.state=()=>seed;
  rand.set=s=>{seed=s>>>0;};
  return rand;
}

async function loadCriticExamples(url='../data/critics/innovations.txt'){
  try{const r=await fetch(url);if(!r.ok)return[];return (await r.text()).split(/\n/).map(l=>l.trim()).filter(Boolean);}catch{return[];}
}
class LogicCritic{
  constructor(ex=[]){this.examples=ex;this.index={};ex.forEach((e,i)=>{this.index[e.toLowerCase()]=i;});this.scale=Math.max(ex.length-1,1);}
  score(g){const k=String(g).toLowerCase();const p=this.index[k]??-1;const b=p>=0?(p+1)/(this.scale+1):0;const n=Math.random()*0.001;const v=b+n;return Math.min(1,Math.max(0,v));}
}
class FeasibilityCritic{
  constructor(ex=[]){this.examples=ex;}
  static j(a,b){const sa=new Set(a),sb=new Set(b);if(!sa.size||!sb.size)return 0;let i=0;for(const x of sa)if(sb.has(x))i++;const u=new Set([...a,...b]).size;return i/u;}
  score(g){const t=String(g).toLowerCase().split(/\s+/);let best=0;for(const ex of this.examples){const s=FeasibilityCritic.j(t,ex.toLowerCase().split(/\s+/));if(s>best)best=s;}const n=Math.random()*0.001;const v=best+n;return Math.min(1,Math.max(0,v));}
}
function initCriticPanel(){
  const root=document.createElement('div');
  root.id='critic-panel';
  Object.assign(root.style,{position:'fixed',top:'10px',right:'10px',background:'rgba(0,0,0,0.7)',color:'#fff',padding:'8px',font:'14px sans-serif',display:'none',zIndex:1000});
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('width','200');svg.setAttribute('height','200');svg.id='critic-chart';
  const table=document.createElement('table');table.id='critic-table';table.style.marginTop='4px';table.style.fontSize='12px';
  root.appendChild(svg);root.appendChild(table);document.body.appendChild(root);
  let highlighted=null;
  function draw(scores){const labels=Object.keys(scores),vals=Object.values(scores),c=100,r=80,step=Math.PI*2/labels.length;svg.innerHTML='';const pts=[];labels.forEach((lb,i)=>{const ang=i*step-Math.PI/2;const rr=r*(vals[i]??0);const x=c+rr*Math.cos(ang);const y=c+rr*Math.sin(ang);pts.push(`${x},${y}`);const lx=c+r*Math.cos(ang);const ly=c+r*Math.sin(ang);const tx=c+(r+12)*Math.cos(ang);const ty=c+(r+12)*Math.sin(ang);const line=document.createElementNS('http://www.w3.org/2000/svg','line');line.setAttribute('x1',c);line.setAttribute('y1',c);line.setAttribute('x2',lx);line.setAttribute('y2',ly);line.setAttribute('stroke','#ccc');svg.appendChild(line);const text=document.createElementNS('http://www.w3.org/2000/svg','text');text.setAttribute('x',tx);text.setAttribute('y',ty);text.setAttribute('font-size','10');text.setAttribute('text-anchor','middle');text.setAttribute('dominant-baseline','middle');text.textContent=lb;svg.appendChild(text);});const poly=document.createElementNS('http://www.w3.org/2000/svg','polygon');poly.setAttribute('points',pts.join(' '));poly.setAttribute('fill','rgba(0,100,250,0.3)');poly.setAttribute('stroke','blue');svg.appendChild(poly);}
  return{show:(scores,el)=>{if(highlighted)highlighted.removeAttribute('stroke');if(el){el.setAttribute('stroke','yellow');highlighted=el;}draw(scores);table.innerHTML=Object.entries(scores).map(([k,v])=>`<tr><th>${k}</th><td>${v.toFixed(2)}</td></tr>`).join('');root.style.display='block';}};
}

let panel,pauseBtn,exportBtn,dropZone
let criticPanel,logicCritic,feasCritic
let current,rand,pop,gen,svg,view,info,running=true
let worker
let telemetry={recordRun(){},recordShare(){}}
let fpsStarted=false
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');clearTimeout(toast.id);toast.id=setTimeout(()=>t.classList.remove('show'),2e3)}
window.toast=toast;
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
  d3.select('svg').remove();
  svg=d3.select('body').append('svg')
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

function selectPoint(d,elem){
  const scores={logic:d.logic??0,feasible:d.feasible??0};
  if(logicCritic&&feasCritic){
    scores.logicCritic=logicCritic.score(`${d.logic}`);
    scores.feasCritic=feasCritic.score(`${d.feasible}`);
    scores.average=(scores.logicCritic+scores.feasCritic)/2;
  }
  criticPanel&&criticPanel.show(scores,elem);
}

function start(p){
  current=p
  rand=lcg(p.seed)
  pop=Array.from({length:p.pop},()=>({logic:rand(),feasible:rand(),strategy:'base'}))
  gen=0
  running=true
  setupView()
  if(!fpsStarted){initFpsMeter(() => running);fpsStarted=true;}
  updateLegend(p.mutations)
  if(worker) worker.terminate()
  worker=new Worker('./worker/evolver.js',{type:'module'})
  worker.onmessage=ev=>{pop=ev.data.pop;rand.set(ev.data.rngState);requestAnimationFrame(step)}
  step()
}

function step(){
  info.text(`gen ${gen}`)
  renderFrontier(view,pop,selectPoint)
  if(!running)return
  if(gen++>=current.gen){worker.terminate();return}
  telemetry.recordRun(1)
  worker.postMessage({pop,rngState:rand.state(),mutations:current.mutations,popSize:current.pop})
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
    worker=new Worker('./worker/evolver.js',{type:'module'})
    worker.onmessage=ev=>{pop=ev.data.pop;rand.set(ev.data.rngState);requestAnimationFrame(step)}
    step()
    toast(t('state_loaded'))
  }catch{toast(t('invalid_file'))}
}

function apply(p){location.hash=toHash(p)}

window.addEventListener('DOMContentLoaded',async()=>{
  telemetry=window.telemetry||telemetry;
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
  csvBtn.addEventListener("click",()=>exportCSV(pop));
  pngBtn.addEventListener("click",exportPNG);
  shareBtn.addEventListener("click",async()=>{
    telemetry.recordShare();
    const url=location.origin+location.pathname+location.hash;
    let pinned=null;
    if(window.PINNER_TOKEN){
      const json=save(pop,rand.state());
      const file=new File([json],"state.json",{type:"application/json"});
      pinned=await pinFiles([file]);
    }
    if(pinned&&pinned.url){
      if(navigator.clipboard){
        try{await navigator.clipboard.writeText(pinned.url);}catch{}}
      toast(`pinned ${pinned.cid}`);
    }else{
      if(navigator.clipboard){
        try{await navigator.clipboard.writeText(url);}catch{}}
      toast(t('link_copied'));
    }
  });
  themeBtn.addEventListener("click",toggleTheme);
  pauseBtn.addEventListener('click',togglePause)
  exportBtn.addEventListener('click',exportState)
  initDragDrop(dropZone,loadState)
  window.dispatchEvent(new HashChangeEvent('hashchange'))
})
window.addEventListener('hashchange',()=>{const p=parseHash();panel.setValues(p);start(p);toast(t('simulation_restarted'))})

})();
