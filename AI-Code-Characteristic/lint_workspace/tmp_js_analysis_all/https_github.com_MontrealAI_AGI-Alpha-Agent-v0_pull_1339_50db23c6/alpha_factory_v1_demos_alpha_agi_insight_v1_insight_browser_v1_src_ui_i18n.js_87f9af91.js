// SPDX-License-Identifier: Apache-2.0
let strings={};
export let currentLanguage='en';
export async function initI18n(){
  const saved=localStorage.getItem('lang');
  const lang=(saved||navigator.language||'en').slice(0,2);
  currentLanguage=lang.startsWith('fr')?'fr':'en';
  const res=await fetch(`src/i18n/${currentLanguage}.json`);
  strings=await res.json();
}
export async function setLanguage(lang){
  currentLanguage=lang;
  localStorage.setItem('lang',lang);
  const res=await fetch(`src/i18n/${lang}.json`);
  strings=await res.json();
}
export function t(key){
  return strings[key]||key;
}
