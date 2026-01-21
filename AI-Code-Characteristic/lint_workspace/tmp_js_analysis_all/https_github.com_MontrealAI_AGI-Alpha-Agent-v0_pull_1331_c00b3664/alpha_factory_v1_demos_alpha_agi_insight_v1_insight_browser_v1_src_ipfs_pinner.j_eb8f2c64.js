/* SPDX-License-Identifier: Apache-2.0 */
import { Web3Storage } from '../lib/bundle.esm.min.js';

export async function pinFiles(files) {
  if (!window.PINNER_TOKEN) return null;
  try {
    const client = new Web3Storage({ token: window.PINNER_TOKEN });
    const cid = await client.put(files);
    const url = `https://ipfs.io/ipfs/${cid}`;
    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(url);
      } catch (_) {
        /* ignore */
      }
    }
    if (typeof window.toast === 'function') {
      window.toast(`pinned ${cid}`);
    }
    return { cid, url };
  } catch (err) {
    console.error('pinFiles failed', err);
    return null;
  }
}
