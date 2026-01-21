const { Simulator } = require('../src/simulator.ts');

jest.setTimeout(10000);

test('500-generation run', async () => {
  const sim = new Simulator({ popSize: 5, generations: 500 });
  let count = 0;
  for await (const g of sim.run()) {
    count = g.gen;
  }
  expect(count).toBe(500);
});

test('memory usage stable', async () => {
  const start = process.memoryUsage().heapUsed;
  const sim = new Simulator({ popSize: 5, generations: 100 });
  for await (const _ of sim.run()) {}
  const end = process.memoryUsage().heapUsed;
  expect(end - start).toBeLessThan(10 * 1024 * 1024);
});
