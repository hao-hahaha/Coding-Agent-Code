// SPDX-License-Identifier: Apache-2.0
/* eslint-env serviceworker */
import {precacheAndRoute} from 'workbox-precaching';

// include translation JSON files in the precache
precacheAndRoute(self.__WB_MANIFEST);

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
