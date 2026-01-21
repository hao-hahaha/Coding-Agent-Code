const { Archive } = require('../src/archive.ts');

beforeEach(async () => {
  indexedDB.deleteDatabase('jest');
});

test('add and list', async () => {
  const a = new Archive('jest');
  await a.open();
  await a.add(1, {seed:1}, [{logic:1,feasible:1,strategy:'s'}]);
  const runs = await a.list();
  expect(runs.length).toBe(1);
  expect(runs[0].gen).toBe(1);
});

test('prune keeps max entries', async () => {
  const a = new Archive('jest');
  await a.open();
  await a.add(1, {}, []);
  await a.add(2, {}, []);
  await a.prune(1);
  const runs = await a.list();
  expect(runs.length).toBe(1);
  expect(runs[0].gen).toBe(2);
});

test('selectParents returns entries', async () => {
  const a = new Archive('jest');
  await a.open();
  await a.add(1, {}, []);
  await a.add(2, {}, []);
  const parents = await a.selectParents(2);
  expect(parents.length).toBe(2);
});
