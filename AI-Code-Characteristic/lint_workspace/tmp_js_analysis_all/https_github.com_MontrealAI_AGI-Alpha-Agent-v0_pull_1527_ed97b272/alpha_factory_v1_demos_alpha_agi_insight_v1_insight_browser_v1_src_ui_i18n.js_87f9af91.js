// SPDX-License-Identifier: Apache-2.0
import enStrings from '../i18n/en.json';

let strings = enStrings;
export let currentLanguage = 'en';

export async function initI18n() {
  const saved = localStorage.getItem('lang');
  const langs = navigator.languages || [navigator.language || 'en'];
  let lang = (saved || langs[0] || 'en').slice(0, 2);
  if (!saved) {
    if (langs.some(l => l.startsWith('zh'))) {
      lang = 'zh';
    } else if (langs.some(l => l.startsWith('fr'))) {
      lang = 'fr';
    } else if (langs.some(l => l.startsWith('es'))) {
      lang = 'es';
    }
  }
  currentLanguage =
    lang.startsWith('fr') ? 'fr' : lang.startsWith('es') ? 'es' : lang.startsWith('zh') ? 'zh' : 'en';
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
