import React, { useEffect, useState } from 'react';
import Plotly from 'plotly.js-dist';

export default function Results() {
  const [data, setData] = useState(null);

  useEffect(() => {
    async function load() {
      const simId = localStorage.getItem('simId');
      if (!simId) return;
      const res = await fetch(`/results/${simId}`);
      if (res.ok) setData(await res.json());
    }
    load();
  }, []);

  useEffect(() => {
    if (data && data.forecast) {
      Plotly.react('cap-chart', [{ x: data.forecast.map(d => d.year), y: data.forecast.map(d => d.capability) }], {});
    }
    if (data && data.pareto) {
      Plotly.react('pareto-chart', [{ x: data.pareto.map(p => p[0]), y: data.pareto.map(p => p[1]), mode: 'markers', type: 'scatter' }], {});
    }
  }, [data]);

  if (!data) return <p>No data</p>;

  return (
    <div>
      <h2>Results</h2>
      <div id="cap-chart" style={{ width: '100%', height: 300 }}></div>
      <div id="pareto-chart" style={{ width: '100%', height: 300 }}></div>
      <table>
        <thead>
          <tr><th>Year</th><th>Capability</th></tr>
        </thead>
        <tbody>
          {data.forecast.map(row => (
            <tr key={row.year}><td>{row.year}</td><td>{row.capability}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
