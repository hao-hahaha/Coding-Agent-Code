// SPDX-License-Identifier: Apache-2.0
import enStrings from '../i18n/en.json';

let strings = enStrings;
export let currentLanguage = 'en';

export async function initI18n() {
  const saved = localStorage.getItem('lang');
  const lang = (saved || navigator.language || 'en').slice(0, 2);
  currentLanguage = lang.startsWith('fr') ? 'fr' : lang.startsWith('es') ? 'es' : 'en';
  try {
    const res = await fetch(`src/i18n/${currentLanguage}.json`);
    strings = { ...enStrings, ...(await res.json()) };
  } catch {
    strings = enStrings;
    currentLanguage = 'en';
  }
}

export async function setLanguage(lang) {
  currentLanguage = lang;
  localStorage.setItem('lang', lang);
  try {
    const res = await fetch(`src/i18n/${lang}.json`);
    strings = { ...enStrings, ...(await res.json()) };
  } catch {
    strings = enStrings;
    currentLanguage = 'en';
  }
}

export function t(key) {
  return strings[key] || enStrings[key] || key;
}
