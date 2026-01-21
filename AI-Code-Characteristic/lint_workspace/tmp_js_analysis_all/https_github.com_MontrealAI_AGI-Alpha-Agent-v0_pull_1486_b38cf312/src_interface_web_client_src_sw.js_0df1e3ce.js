/* eslint-disable no-restricted-globals */
importScripts('workbox-sw.js');
import {precacheAndRoute} from 'workbox-precaching';
import {registerRoute} from 'workbox-routing';
import {CacheFirst} from 'workbox-strategies';
import {ExpirationPlugin} from 'workbox-expiration';

const CACHE_VERSION = 'insight-v1';
workbox.core.setCacheNameDetails({prefix: CACHE_VERSION});

precacheAndRoute(self.__WB_MANIFEST);

registerRoute(
  ({request, url}) =>
    request.destination === 'script' ||
    request.destination === 'worker' ||
    request.destination === 'font' ||
    url.pathname.endsWith('.wasm'),
  new CacheFirst({
    cacheName: `${CACHE_VERSION}-assets`,
    plugins: [
      new ExpirationPlugin({maxEntries: 50, maxAgeSeconds: 30 * 24 * 60 * 60})
    ],
  })
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
