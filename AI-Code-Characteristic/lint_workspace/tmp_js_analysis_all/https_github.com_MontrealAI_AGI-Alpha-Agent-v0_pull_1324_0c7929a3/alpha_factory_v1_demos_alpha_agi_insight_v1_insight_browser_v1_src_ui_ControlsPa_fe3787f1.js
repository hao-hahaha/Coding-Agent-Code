// SPDX-License-Identifier: Apache-2.0
export function initControls(params,onChange){
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
    onChange({seed:+seed.value,pop:+pop.value,gen:+gen.value,mutations:muts});
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
