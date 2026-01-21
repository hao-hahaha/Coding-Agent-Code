const { Simulator } = require('../src/simulator.ts');
const { mineMemes, saveMemes, loadMemes } = require('@insight-src/memeplex.ts');

beforeEach(() => {
  indexedDB.deleteDatabase('memeplex');
});

test('meme counts increase during run', async () => {
  const runs = [];
  const sim = Simulator.run({ popSize: 3, generations: 3 });
  for await (const g of sim) {
    const edges = g.population.map(p => ({ from: p.strategy || 'x', to: p.strategy || 'x' }));
    runs.push({ edges });
    await saveMemes(mineMemes(runs, 1));
  }
  const memes = await loadMemes();
  expect(memes.some(m => m.count > 1)).toBe(true);
});
