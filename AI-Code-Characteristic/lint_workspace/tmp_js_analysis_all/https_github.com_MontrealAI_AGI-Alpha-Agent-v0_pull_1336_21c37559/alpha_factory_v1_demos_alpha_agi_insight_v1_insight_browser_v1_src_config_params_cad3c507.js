// SPDX-License-Identifier: Apache-2.0
export const defaults={seed:42,pop:80,gen:60,mutations:['gaussian']};
export function parseHash(h=window.location.hash){
  if(!h || h==='#'){
    try{
      const stored=localStorage.getItem('insightParams');
      if(stored){
        const p=JSON.parse(stored);
        return{
          seed:p.seed??defaults.seed,
          pop:p.pop??defaults.pop,
          gen:p.gen??defaults.gen,
          mutations:p.mutations??defaults.mutations
        };
      }
    }catch{}
  }
  const q=new URLSearchParams(h.replace(/^#/,''));
  return{
    seed:+q.get('seed')||defaults.seed,
    pop:+q.get('pop')||defaults.pop,
    gen:+q.get('gen')||defaults.gen,
    mutations:(q.get('mut')||defaults.mutations.join(',')).split(',').filter(Boolean)
  };
}
export function toHash(p){
  const q=new URLSearchParams();
  q.set('seed',p.seed);q.set('pop',p.pop);q.set('gen',p.gen);
  if(p.mutations) q.set('mut',p.mutations.join(','));
  return'#'+q.toString();
}
