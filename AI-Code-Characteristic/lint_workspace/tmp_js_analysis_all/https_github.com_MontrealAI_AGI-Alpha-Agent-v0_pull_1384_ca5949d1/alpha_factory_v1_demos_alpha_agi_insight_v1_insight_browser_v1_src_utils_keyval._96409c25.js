// SPDX-License-Identifier: Apache-2.0
export function createStore(dbName, storeName) {
  const dbp = new Promise((resolve, reject) => {
    const req = indexedDB.open(dbName, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(storeName);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return { dbp, storeName };
}

async function withStore(type, store, fn) {
  const db = await store.dbp;
  return new Promise((resolve, reject) => {
    const tx = db.transaction(store.storeName, type);
    const st = tx.objectStore(store.storeName);
    const req = fn(st);
    tx.oncomplete = () => resolve(req?.result);
    tx.onerror = () => reject(tx.error);
  });
}

export function get(key, store) {
  return withStore('readonly', store, (s) => s.get(key));
}
export function set(key, val, store) {
  return withStore('readwrite', store, (s) => s.put(val, key));
}
export function del(key, store) {
  return withStore('readwrite', store, (s) => s.delete(key));
}
export function keys(store) {
  return withStore('readonly', store, (s) => s.getAllKeys());
}
export function values(store) {
  return withStore('readonly', store, (s) => s.getAll());
}
