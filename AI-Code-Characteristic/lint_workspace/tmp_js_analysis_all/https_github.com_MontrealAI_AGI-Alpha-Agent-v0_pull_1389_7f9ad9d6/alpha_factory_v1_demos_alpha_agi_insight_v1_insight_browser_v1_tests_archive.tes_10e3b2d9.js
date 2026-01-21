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
  const parents = await a.selectParents(1);
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
