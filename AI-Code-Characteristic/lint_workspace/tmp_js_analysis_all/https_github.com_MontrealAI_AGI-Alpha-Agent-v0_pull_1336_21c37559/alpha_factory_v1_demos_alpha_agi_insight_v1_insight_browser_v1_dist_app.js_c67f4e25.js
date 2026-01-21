(function() {
/* Placeholder for web3.storage bundle.esm.min.js
   The actual file should be downloaded from:
   https://cdn.jsdelivr.net/npm/web3.storage/dist/bundle.esm.min.js
*/
function Web3Storage(){ throw new Error('web3.storage not bundled'); }

// SPDX-License-Identifier: Apache-2.0
const defaults={seed:42,pop:80,gen:60,mutations:['gaussian']};
function parseHash(h=window.location.hash){
  if(!h||h==='#'){
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
  const q=new URLSearchParams(h.replace(/^#/,''));
  return{
    seed:+q.get('seed')||defaults.seed,
    pop:+q.get('pop')||defaults.pop,
    gen:+q.get('gen')||defaults.gen,
    mutations:(q.get('mut')||defaults.mutations.join(',')).split(',').filter(Boolean)
  };
}
function toHash(p){
  const q=new URLSearchParams();
  q.set('seed',p.seed);q.set('pop',p.pop);q.set('gen',p.gen);
  if(p.mutations) q.set('mut',p.mutations.join(','));
  return'#'+q.toString();
}

// SPDX-License-Identifier: Apache-2.0
function initControls(params,onChange){
  const root=document.getElementById('controls');
  root.innerHTML=`<label>Seed <input id="seed" type="number" min="0"></label>
<label>Population <input id="pop" type="number" min="1"></label>
<label>Generations <input id="gen" type="number" min="1"></label>
<label><input id="gaussian" type="checkbox"> gaussian</label>
<label><input id="swap" type="checkbox"> swap</label>
<label><input id="jump" type="checkbox"> jump</label>
<label><input id="scramble" type="checkbox"> scramble</label>
<button id="pause">Pause</button>
<button id="export">Export</button>
<div id="drop">Drop JSON here</div>`;
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
        drop=root.querySelector('#drop');
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
function renderFrontier(svg, pop, x, y) {
  const front = paretoFront(pop).sort((a, b) => a.logic - b.logic);

  const area = d3
    .area()
    .x((d) => x(d.logic))
    .y0(y.range()[0])
    .y1((d) => y(d.feasible));

  let g = svg.select('g#frontier');
  if (g.empty()) g = svg.append('g').attr('id', 'frontier');

  g.selectAll('path')
    .data([front])
    .join('path')
    .attr('fill', 'rgba(0,175,255,0.2)')
    .attr('stroke', 'none')
    .attr('d', area);

  let dots = svg.select('g#dots');
  if (dots.empty()) dots = svg.append('g').attr('id', 'dots');

  if (pop.length > 5000) {
    dots.selectAll('circle').remove();
    const frontSet = new Set(front);
    drawPoints(dots, pop, x, y, (d) => {
      if (frontSet.has(d)) return strategyColors.front;
      return strategyColors[d.strategy] || strategyColors.base;
    });
  } else {
    const node = dots.node();
    const fo = node.querySelector('foreignObject#canvas-layer');
    if (fo) fo.remove();

    dots
      .selectAll('circle')
      .data(pop)
      .join('circle')
      .attr('cx', (d) => x(d.logic))
      .attr('cy', (d) => y(d.feasible))
      .attr('r', 3)
      .attr('fill', (d) => {
        if (front.includes(d)) return strategyColors.front;
        return strategyColors[d.strategy] || strategyColors.base;
      })
      .attr('filter', (d) => (front.includes(d) ? 'url(#glow)' : null))
      .on('mousemove', (ev, d) =>
        showTooltip(
          ev.pageX + 6,
          ev.pageY + 6,
          `logic: ${d.logic.toFixed(2)}\nfeas: ${d.feasible.toFixed(2)}`
        )
      )
      .on('mouseleave', hideTooltip);
  }
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


function lcg(seed){
  function rand(){
    seed=Math.imul(1664525,seed)+1013904223>>>0;
    return seed/2**32;
  }
  rand.state=()=>seed;
  rand.set=s=>{seed=s>>>0;};
  return rand;
}

let panel,pauseBtn,exportBtn,dropZone
let current,rand,pop,gen,svg,view,x,y,info,running=true
let worker
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');clearTimeout(toast.id);toast.id=setTimeout(()=>t.classList.remove('show'),2e3)}
window.toast=toast;

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
  x=d3.scaleLinear().domain([0,1]).range([40,460])
  y=d3.scaleLinear().domain([0,1]).range([460,40])
  addGlow(svg)
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

function start(p){
  current=p
  rand=lcg(p.seed)
  pop=Array.from({length:p.pop},()=>({logic:rand(),feasible:rand(),strategy:'base'}))
  gen=0
  running=true
  setupView()
  updateLegend(p.mutations)
  if(worker) worker.terminate()
  worker=new Worker('./worker/evolver.js',{type:'module'})
  worker.onmessage=ev=>{pop=ev.data.pop;rand.set(ev.data.rngState);requestAnimationFrame(step)}
  step()
}

function step(){
  info.text(`gen ${gen}`)
  renderFrontier(view,pop,x,y)
  if(!running)return
  if(gen++>=current.gen){worker.terminate();return}
  worker.postMessage({pop,rngState:rand.state(),mutations:current.mutations,popSize:current.pop})
}

function togglePause(){
  running=!running
  pauseBtn.textContent=running?'Pause':'Resume'
  if(running)requestAnimationFrame(step)
}

function exportState(){
  pop.gen=gen
  const json=save(pop,rand.state())
  const a=document.createElement('a')
  a.href=URL.createObjectURL(new Blob([json],{type:'application/json'}))
  a.download='state.json'
  a.click()
  URL.revokeObjectURL(a.href)
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
    pauseBtn.textContent='Pause'
    setupView()
    updateLegend(current.mutations)
    if(worker) worker.terminate()
    worker=new Worker('./worker/evolver.js',{type:'module'})
    worker.onmessage=ev=>{pop=ev.data.pop;rand.set(ev.data.rngState);requestAnimationFrame(step)}
    step()
    toast('state loaded')
  }catch{toast('invalid file')}
}

function apply(p){location.hash=toHash(p)}

window.addEventListener('DOMContentLoaded',()=>{
  loadTheme()
  panel=initControls(parseHash(),apply)
  pauseBtn=panel.pauseBtn
  exportBtn=panel.exportBtn
  dropZone=panel.dropZone
  const tb=document.getElementById("toolbar");
  const csvBtn=document.createElement("button");
  csvBtn.textContent="CSV";
  const pngBtn=document.createElement("button");
  pngBtn.textContent="PNG";
  const shareBtn=document.createElement("button");
  shareBtn.textContent="Share";
  const themeBtn=document.createElement("button");
  themeBtn.textContent="Theme";
  tb.appendChild(csvBtn);
  tb.appendChild(pngBtn);
  tb.appendChild(shareBtn);
  tb.appendChild(themeBtn);
  csvBtn.addEventListener("click",()=>exportCSV(pop));
  pngBtn.addEventListener("click",exportPNG);
  shareBtn.addEventListener("click",async()=>{
    const snippet=`<iframe src="${location.origin+location.pathname+location.hash}"></iframe>`;
    if(navigator.clipboard){
      try{await navigator.clipboard.writeText(snippet);}catch{}}
    toast('iframe snippet copied');
    if(window.PINNER_TOKEN){
      const file=new File([snippet],"snippet.html",{type:"text/html"});
      await pinFiles([file]);
    }
  });
  themeBtn.addEventListener("click",toggleTheme);
  pauseBtn.addEventListener('click',togglePause)
  exportBtn.addEventListener('click',exportState)
  initDragDrop(dropZone,loadState)
  window.dispatchEvent(new HashChangeEvent('hashchange'))
})
window.addEventListener('hashchange',()=>{const p=parseHash();panel.setValues(p);start(p);toast('simulation restarted')})

})();
