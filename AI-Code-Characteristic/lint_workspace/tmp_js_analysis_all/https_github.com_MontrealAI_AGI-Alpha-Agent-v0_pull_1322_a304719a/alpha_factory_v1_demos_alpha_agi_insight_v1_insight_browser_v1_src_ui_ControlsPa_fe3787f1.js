// SPDX-License-Identifier: Apache-2.0
export function initControls(params,onChange){
  const root=document.getElementById('controls');
  root.innerHTML=`<label>Seed <input id="seed" type="number" min="0"></label>
<label>Population <input id="pop" type="number" min="1"></label>
<label>Generations <input id="gen" type="number" min="1"></label>
<button id="pause">Pause</button>
<button id="export">Export</button>
<div id="drop">Drop JSON here</div>`;
  const seed=root.querySelector('#seed'),
        pop=root.querySelector('#pop'),
        gen=root.querySelector('#gen');
  function update(p){
    seed.value=p.seed;
    pop.value=p.pop;
    gen.value=p.gen;
  }
  update(params);
  function emit(){
    onChange({seed:+seed.value,pop:+pop.value,gen:+gen.value});
  }
  seed.addEventListener('change',emit);
  pop.addEventListener('change',emit);
  gen.addEventListener('change',emit);
  const pause=root.querySelector('#pause'),
        exportBtn=root.querySelector('#export'),
        drop=root.querySelector('#drop');
  return{setValues:update,pauseBtn:pause,exportBtn,dropZone:drop};
}
