/* SPDX-License-Identifier: Apache-2.0 */
/* eslint-env serviceworker */
const CACHE = 'v3';
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then(async (cache) => {
        const assets = [
          'assets/pyodide/pyodide.js',
          'assets/pyodide/pyodide.asm.wasm',
        ];
        await cache.addAll(assets);
      })
      .catch(() => undefined),
  );
  self.skipWaiting();
});
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
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        try {
          const resp = await fetch(event.request);
          if (resp.ok) {
            cache.put(event.request, resp.clone());
          }
          return resp;
        } catch (err) {
          const cached =
            (await cache.match(event.request)) ||
            (await cache.match(`pyodide/${url.pathname.split('/').pop()}`));
          return cached || Promise.reject(err);
        }
      }),
    );
    return;
  }
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
