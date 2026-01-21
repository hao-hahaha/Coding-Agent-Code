// SPDX-License-Identifier: Apache-2.0
/* eslint-env serviceworker */
importScripts('workbox-sw.js');
import {precacheAndRoute} from 'workbox-precaching';
import {registerRoute} from 'workbox-routing';
import {CacheFirst} from 'workbox-strategies';

const CACHE_VERSION = 'insight-v1';
workbox.core.setCacheNameDetails({prefix: CACHE_VERSION});

// include translation JSON files in the precache
precacheAndRoute(self.__WB_MANIFEST);

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
