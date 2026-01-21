// SPDX-License-Identifier: Apache-2.0
export function initControls(params,onChange){
  const root=document.getElementById('controls');
  root.innerHTML=`<label>Seed <input id="seed" type="number" min="0" aria-label="Seed value" tabindex="1"></label>
<label>Population <input id="pop" type="number" min="1" aria-label="Population size" tabindex="2"></label>
<label>Generations <input id="gen" type="number" min="1" aria-label="Number of generations" tabindex="3"></label>
<label><input id="gaussian" type="checkbox" aria-label="Enable gaussian mutation" tabindex="4"> gaussian</label>
<label><input id="swap" type="checkbox" aria-label="Enable swap mutation" tabindex="5"> swap</label>
<label><input id="jump" type="checkbox" aria-label="Enable jump mutation" tabindex="6"> jump</label>
<label><input id="scramble" type="checkbox" aria-label="Enable scramble mutation" tabindex="7"> scramble</label>
<button id="pause" role="button" aria-label="Pause simulation" tabindex="8">Pause</button>
<button id="export" role="button" aria-label="Export data" tabindex="9">Export</button>
<div id="drop" role="button" aria-label="Drop JSON here" tabindex="10">Drop JSON here</div>`;
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
