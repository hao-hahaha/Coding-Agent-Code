// SPDX-License-Identifier: Apache-2.0
export function initControls(params,onChange){
  const root=document.getElementById('controls');
  root.innerHTML=`<label>Seed <input id="seed" type="number" min="0"></label>
<label>Population <input id="pop" type="number" min="1"></label>
<label>Generations <input id="gen" type="number" min="1"></label>`;
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
  return{setValues:update};
}
