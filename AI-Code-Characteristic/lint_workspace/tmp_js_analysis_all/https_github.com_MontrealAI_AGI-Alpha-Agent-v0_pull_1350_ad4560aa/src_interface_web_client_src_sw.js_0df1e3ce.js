/* eslint-disable no-restricted-globals */
import {precacheAndRoute} from 'workbox-precaching';
import {registerRoute} from 'workbox-routing';
import {CacheFirst} from 'workbox-strategies';
import {ExpirationPlugin} from 'workbox-expiration';

precacheAndRoute(self.__WB_MANIFEST);

registerRoute(
  ({request, url}) =>
    request.destination === 'script' ||
    request.destination === 'worker' ||
    request.destination === 'font' ||
    url.pathname.endsWith('.wasm'),
  new CacheFirst({
    cacheName: 'assets-cache',
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
