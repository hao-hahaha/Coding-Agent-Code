// SPDX-License-Identifier: Apache-2.0
/* eslint-env serviceworker */
import {precacheAndRoute} from 'workbox-precaching';

precacheAndRoute(self.__WB_MANIFEST);
