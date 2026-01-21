// SPDX-License-Identifier: Apache-2.0
export function paretoFront(pop) {
  if (pop.length === 0) return [];

  // Sort by logic (desc) then feasible (desc) and scan once.
  const sorted = [...pop].sort(
    (a, b) => b.logic - a.logic || b.feasible - a.feasible,
  );

  const front = [];
  let bestFeasible = -Infinity;
  for (const p of sorted) {
    if (p.feasible >= bestFeasible) {
      front.push(p);
      bestFeasible = p.feasible;
    }
  }

  return front;
}
