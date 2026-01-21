import test from 'node:test';
import assert from 'node:assert/strict';
import { Simulator } from '../src/simulator.ts';

test('run initializes within 70ms', async () => {
  const start = performance.now();
  const sim = Simulator.run({ popSize: 1, generations: 1 });
  await sim.next();
  const elapsed = performance.now() - start;
  assert.ok(elapsed < 70, `init took ${elapsed}ms`);
});
