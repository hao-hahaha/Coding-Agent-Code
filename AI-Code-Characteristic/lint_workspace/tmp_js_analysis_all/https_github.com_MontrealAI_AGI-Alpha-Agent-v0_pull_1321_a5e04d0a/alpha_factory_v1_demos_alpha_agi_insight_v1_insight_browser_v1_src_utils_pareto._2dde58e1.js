// SPDX-License-Identifier: Apache-2.0
export function paretoFront(pop) {
  const front = [];
  for (const a of pop) {
    let dominated = false;
    for (const b of pop) {
      if (a === b) continue;
      if (
        b.logic >= a.logic &&
        b.feasible >= a.feasible &&
        (b.logic > a.logic || b.feasible > a.feasible)
      ) {
        dominated = true;
        break;
      }
    }
    if (!dominated) front.push(a);
  }
  return front;
}
