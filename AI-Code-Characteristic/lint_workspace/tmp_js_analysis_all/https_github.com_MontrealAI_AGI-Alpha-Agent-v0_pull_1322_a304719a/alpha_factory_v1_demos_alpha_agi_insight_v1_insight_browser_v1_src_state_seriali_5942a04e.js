// SPDX-License-Identifier: Apache-2.0
export function save(pop, rngState) {
  const data = {
    gen: pop.gen ?? 0,
    pop: Array.from(pop, (d) => ({ logic: d.logic, feasible: d.feasible, front: d.front })),
    rngState,
  };
  return JSON.stringify(data);
}

export function load(json) {
  const data = JSON.parse(json);
  if (!Array.isArray(data.pop)) throw new Error('Invalid population');
  const pop = data.pop.map((d) => ({ logic: d.logic, feasible: d.feasible, front: d.front }));
  pop.gen = data.gen ?? 0;
  return { pop, rngState: data.rngState, gen: data.gen ?? 0 };
}
