// SPDX-License-Identifier: Apache-2.0
export const defaults={seed:42,pop:80,gen:60};
export function parseHash(h=window.location.hash){
  const q=new URLSearchParams(h.replace(/^#/,''));
  return{seed:+q.get('seed')||defaults.seed,pop:+q.get('pop')||defaults.pop,gen:+q.get('gen')||defaults.gen};
}
export function toHash(p){
  const q=new URLSearchParams();
  q.set('seed',p.seed);q.set('pop',p.pop);q.set('gen',p.gen);
  return'#'+q.toString();
}
