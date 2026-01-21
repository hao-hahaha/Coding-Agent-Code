// SPDX-License-Identifier: Apache-2.0
import {t,setLanguage,currentLanguage} from './i18n.js';
export function initControls(params,onChange){
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
