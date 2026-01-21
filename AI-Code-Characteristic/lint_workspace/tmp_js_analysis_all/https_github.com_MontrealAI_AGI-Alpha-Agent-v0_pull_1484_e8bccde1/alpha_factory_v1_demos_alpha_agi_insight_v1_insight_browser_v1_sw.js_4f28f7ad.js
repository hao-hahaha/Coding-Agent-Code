// SPDX-License-Identifier: Apache-2.0
/* eslint-env serviceworker */
importScripts('workbox-sw.js');
import {precacheAndRoute} from 'workbox-precaching';
import {registerRoute} from 'workbox-routing';
import {CacheFirst} from 'workbox-strategies';

// include translation JSON files in the precache
precacheAndRoute(self.__WB_MANIFEST);

registerRoute(
  ({request, url}) =>
    request.destination === 'script' ||
    request.destination === 'worker' ||
    request.destination === 'font' ||
    url.pathname.endsWith('.wasm') ||
    (url.pathname.includes('/ipfs/') && url.pathname.endsWith('.json')),
  new CacheFirst({cacheName: 'insight-v1'})
);

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
