/* SPDX-License-Identifier: Apache-2.0 */
/* eslint-env serviceworker */
const CACHE = 'v1';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names.map((name) => (name !== CACHE ? caches.delete(name) : undefined)),
      ),
    ),
  );
  self.clients.claim();
});
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.open(CACHE).then((cache) =>
      cache.match(event.request).then(
        (cached) =>
          cached ||
          fetch(event.request)
            .then((resp) => {
              if (resp.ok) {
                cache.put(event.request, resp.clone());
              }
              return resp;
            })
            .catch(() => cached),
      ),
    ),
  );
});
