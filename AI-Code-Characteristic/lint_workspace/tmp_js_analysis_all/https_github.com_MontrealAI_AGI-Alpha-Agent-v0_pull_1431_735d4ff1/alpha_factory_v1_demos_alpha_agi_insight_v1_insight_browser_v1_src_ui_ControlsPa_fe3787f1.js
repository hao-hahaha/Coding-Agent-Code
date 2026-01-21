// SPDX-License-Identifier: Apache-2.0
import {t,setLanguage,currentLanguage} from './i18n.js';
const MAX_VAL = 500;
export function initControls(params,onChange){
  const root=document.getElementById('controls');
  root.innerHTML=`<label>${t('seed')} <input id="seed" type="number" min="0" aria-label="${t('seed')}" tabindex="1"></label>
<label>${t('population')} <input id="pop" type="number" min="1" max="${MAX_VAL}" aria-label="${t('population')}" tabindex="2"></label>
<label>${t('generations')} <input id="gen" type="number" min="1" max="${MAX_VAL}" aria-label="${t('generations')}" tabindex="3"></label>
<label><input id="gaussian" type="checkbox" aria-label="${t('gaussian')}" tabindex="4"> ${t('gaussian')}</label>
<label><input id="swap" type="checkbox" aria-label="${t('swap')}" tabindex="5"> ${t('swap')}</label>
<label><input id="jump" type="checkbox" aria-label="${t('jump')}" tabindex="6"> ${t('jump')}</label>
  <label><input id="scramble" type="checkbox" aria-label="${t('scramble')}" tabindex="7"> ${t('scramble')}</label>
  <label><input id="adaptive" type="checkbox" aria-label="${t('adaptive')}" tabindex="8"> ${t('adaptive')}</label>
  <button id="pause" role="button" aria-label="${t('pause')}" tabindex="9">${t('pause')}</button>
  <button id="export" role="button" aria-label="${t('export')}" tabindex="10">${t('export')}</button>
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
        scramble=root.querySelector('#scramble'),
        adaptive=root.querySelector('#adaptive');
  function update(p){
    seed.value=p.seed;
    pop.value=Math.min(p.pop,MAX_VAL);
    gen.value=Math.min(p.gen,MAX_VAL);
    const set=new Set(p.mutations||[]);
    gauss.checked=set.has('gaussian');
    swap.checked=set.has('swap');
    jump.checked=set.has('jump');
    scramble.checked=set.has('scramble');
    adaptive.checked=p.adaptive||false;
  }
  update(params);
  function emit(){
    const muts=[gauss,swap,jump,scramble].filter(c=>c.checked).map(c=>c.id);
    let popVal=Math.min(+pop.value,MAX_VAL);
    let genVal=Math.min(+gen.value,MAX_VAL);
    const info={popClamped:popVal!==+pop.value,genClamped:genVal!==+gen.value};
    pop.value=popVal;
    gen.value=genVal;
    const p={seed:+seed.value,pop:popVal,gen:genVal,mutations:muts,adaptive:adaptive.checked};
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
    adaptive.addEventListener('change',emit);
  const pause=root.querySelector('#pause'),
        exportBtn=root.querySelector('#export'),
        drop=root.querySelector('#drop'),
        langSel=root.querySelector('#lang');
  langSel.value=currentLanguage;
  langSel.addEventListener('change',async()=>{await setLanguage(langSel.value);location.reload();});
  return{setValues:update,pauseBtn:pause,exportBtn,dropZone:drop};
}
