// SPDX-License-Identifier: Apache-2.0
const { mutateEvaluator } = require('../src/evaluator_genome.ts');
const { lcg } = require('../src/utils/rng.js');

test('mutateEvaluator changes weights and prompt', () => {
  const rand = lcg(1);
  const base = { weights: { logic: 0.7, feasible: 0.3 }, prompt: 'judge idea' };
  const m = mutateEvaluator(base, rand);
  expect(m.weights.logic + m.weights.feasible).toBeCloseTo(1, 5);
  expect(m.weights.logic).not.toBeCloseTo(base.weights.logic);
  expect(m.prompt).not.toBe(base.prompt);
});
