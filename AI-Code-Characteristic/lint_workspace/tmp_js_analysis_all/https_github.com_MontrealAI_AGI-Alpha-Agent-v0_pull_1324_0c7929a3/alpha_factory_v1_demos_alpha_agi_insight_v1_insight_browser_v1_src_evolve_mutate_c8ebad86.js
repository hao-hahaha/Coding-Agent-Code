// SPDX-License-Identifier: Apache-2.0
export function mutate(pop, rand, strategies) {
  const clamp = (v) => Math.min(1, Math.max(0, v));
  const mutants = [];
  for (const d of pop) {
    for (const s of strategies) {
      switch (s) {
        case 'gaussian':
          mutants.push({
            logic: clamp(d.logic + (rand() - 0.5) * 0.12),
            feasible: clamp(d.feasible + (rand() - 0.5) * 0.12),
            strategy: s,
          });
          break;
        case 'swap': {
          const other = pop[Math.floor(rand() * pop.length)];
          mutants.push({ logic: other.logic, feasible: d.feasible, strategy: s });
          break;
        }
        case 'jump':
          mutants.push({ logic: rand(), feasible: rand(), strategy: s });
          break;
        case 'scramble': {
          const other = pop[Math.floor(rand() * pop.length)];
          mutants.push({ logic: d.logic, feasible: other.feasible, strategy: s });
          break;
        }
      }
    }
  }
  return pop.concat(mutants);
}
