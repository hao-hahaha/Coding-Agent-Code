// SPDX-License-Identifier: Apache-2.0
const { Archive } = require('../src/archive.ts');

beforeEach(async () => {
  indexedDB.deleteDatabase('jest');
});

test('add and list', async () => {
  const a = new Archive('jest');
  await a.open();
  await a.add(42, {pop:1}, [{logic:1,feasible:1}]);
  const runs = await a.list();
  expect(runs.length).toBe(1);
  expect(runs[0].seed).toBe(42);
  expect(runs[0].paretoFront.length).toBe(1);
});

test('prune keeps max entries', async () => {
  const a = new Archive('jest');
  await a.open();
  await a.add(1, {}, [{logic:0.1,feasible:0.1}]);
  await a.add(2, {}, [{logic:0.9,feasible:0.9}]);
  await a.prune(1);
  const runs = await a.list();
  expect(runs.length).toBe(1);
  expect(runs[0].seed).toBe(2);
});

test('selectParents returns entries', async () => {
  const a = new Archive('jest');
  await a.open();
  await a.add(1, {}, [{logic:0.2,feasible:0.2}]);
  await a.add(2, {}, [{logic:0.8,feasible:0.8}]);
  const parents = await a.selectParents(1, 1, 1, () => 0.5);
  expect(parents.length).toBe(1);
  expect([1,2]).toContain(parents[0].seed);
});

test('parents saved and retrieved', async () => {
  const a = new Archive('jest');
  await a.open();
  const id = await a.add(3, {}, [], [1, 2]);
  const runs = await a.list();
  const run = runs.find((r) => r.id === id);
  expect(run.parents).toEqual([1, 2]);
});

test('prune removes unused evaluators', async () => {
  const a = new Archive('jest');
  await a.open();
  const evalId = await a.addEvaluator({ weights: { logic: 0.5, feasible: 0.5 }, prompt: 'x' });
  await a.add(1, {}, [{logic:0.1,feasible:0.1}], [], evalId);
  await a.prune(0);
  const evals = await a.listEvaluators();
  expect(evals.length).toBe(0);
});

test('add generates unique ids', async () => {
  const a = new Archive('jest');
  await a.open();
  const id1 = await a.add(1, {}, []);
  const id2 = await a.add(2, {}, []);
  expect(id1).not.toBe(id2);
  const runs = await a.list();
  expect(runs.length).toBe(2);
});

test('in-memory fallback triggers toast', async () => {
  const orig = global.indexedDB;
  delete global.indexedDB;
  window.toast = jest.fn();
  const a = new Archive('jest');
  await a.open();
  expect(window.toast).toHaveBeenCalledWith('Archive disabled (no storage access)');
  await a.add(3, {}, []);
  const runs = await a.list();
  expect(runs.length).toBe(1);
  global.indexedDB = orig;
});

test('auto prune retains latest 50 runs', async () => {
  const a = new Archive('jest');
  await a.open();
  for (let i = 0; i < 55; i++) {
    await a.add(i, {}, [{ logic: 0, feasible: 0 }]);
  }
  const runs = await a.list();
  expect(runs.length).toBe(50);
  expect(runs[0].seed).toBe(5);
});
