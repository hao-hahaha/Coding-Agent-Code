// SPDX-License-Identifier: Apache-2.0
const { ReplayDB } = require('../src/replay.ts');

beforeEach(() => {
  indexedDB.deleteDatabase('jest');
  indexedDB.deleteDatabase('jest2');
});

test('share and import frames maintain order and cid', async () => {
  const db1 = new ReplayDB('jest');
  await db1.open();
  let parent = null;
  for (let i = 0; i < 3; i++) {
    parent = await db1.addFrame(parent, { step: i });
  }
  const finalId = parent;

  const { cid, data } = await db1.share(finalId);

  const db2 = new ReplayDB('jest2');
  await db2.open();
  const importedId = await db2.importFrames(data);

  const thread1 = await db1.exportThread(finalId);
  const thread2 = await db2.exportThread(importedId);

  expect(thread2).toEqual(thread1);

  const cid1 = await db1.computeCid(finalId);
  const cid2 = await db2.computeCid(importedId);
  expect(cid1).toBe(cid);
  expect(cid2).toBe(cid);
});
