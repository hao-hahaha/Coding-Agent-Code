// SPDX-License-Identifier: Apache-2.0
/* eslint-env serviceworker */
importScripts('workbox-sw.js');
import {precacheAndRoute} from 'workbox-precaching';
import {registerRoute} from 'workbox-routing';
import {CacheFirst} from 'workbox-strategies';

// replaced during build
const CACHE_VERSION = '0.1.0';
workbox.core.setCacheNameDetails({prefix: CACHE_VERSION});

// include translation JSON files in the precache
precacheAndRoute([{"revision":"05b379e458f8c7ee748b7f4ae174b0ca","url":"index.html"},{"revision":"7035322644796c803c6e72e9838d2440","url":"insight.bundle.js"},{"revision":"065f49acd9cb81fd67c1fb4e2d059f37","url":"d3.v7.min.js"},{"revision":"a19de222fc8049e3c80cfca67067f04a","url":"wasm_llm/README.md"},{"revision":"8a80554c91d9fca8acb82f023de02f11","url":"wasm/packages.json"},{"revision":"09999c1ce2a74c2b827091f9a2259142","url":"wasm/pyodide_py.tar"},{"revision":"f05f0ad3c5727bb9441b1259c4074e27","url":"wasm/pyodide.asm.wasm"},{"revision":"04269d3b11e931c799adf682cd16599d","url":"wasm/pyodide.js"},{"revision":"e1a14b3cbb3ce35ce4fa91cc3f42615f","url":"data/critics/innovations.txt"},{"revision":"4721ebadc209ba0d0bbda13c471b2455","url":"src/i18n/en.json"},{"revision":"b36ffcbd02d5217cccb505d3757488d1","url":"src/i18n/es.json"},{"revision":"546c78f7e44fc37d41a66eafd92c1e4e","url":"src/i18n/fr.json"},{"revision":"942d2b657e9ad8dd9e3e122017dd454e","url":"src/i18n/zh.json"},{"revision":"233fb5ac842b83f84652451be21d9191","url":"insight_browser_quickstart.pdf"}]);

registerRoute(
  ({request, url}) =>
    request.destination === 'script' ||
    request.destination === 'worker' ||
    request.destination === 'font' ||
    url.pathname.endsWith('.wasm') ||
    (url.pathname.includes('/ipfs/') && url.pathname.endsWith('.json')),
  new CacheFirst({cacheName: `${CACHE_VERSION}-assets`})
);

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names.map((name) => {
          if (!name.startsWith(CACHE_VERSION)) {
            return caches.delete(name);
          }
          return undefined;
        }),
      ),
    ),
  );
});
