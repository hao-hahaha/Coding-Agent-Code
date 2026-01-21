import React, { useState } from 'react';

export default function SimConfig() {
  const [horizon, setHorizon] = useState(5);
  const [pop, setPop] = useState(6);
  const [gen, setGen] = useState(3);

  async function run() {
    const res = await fetch('/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ horizon, pop_size: pop, generations: gen })
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('simId', data.id);
    }
  }

  return (
    <div>
      <h2>Simulation Parameters</h2>
      <label>
        Horizon
        <input type="number" value={horizon} onChange={e => setHorizon(+e.target.value)} />
      </label>
      <label>
        Population
        <input type="number" value={pop} onChange={e => setPop(+e.target.value)} />
      </label>
      <label>
        Generations
        <input type="number" value={gen} onChange={e => setGen(+e.target.value)} />
      </label>
      <button onClick={run}>Start</button>
    </div>
  );
}
