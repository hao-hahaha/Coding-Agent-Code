async function loadData() {
  const forecast = await fetch('forecast.json').then(r => r.json());
  const population = await fetch('population.json').then(r => r.json());

  const years = forecast.map(p => p.year);
  const capability = forecast.map(p => p.capability);

  Plotly.newPlot('capability', [
    { x: years, y: capability, mode: 'lines+markers', name: 'Capability' }
  ], {
    title: 'AGI Capability Curve',
    xaxis: { title: 'Year' },
    yaxis: { title: 'Capability' }
  });

  Plotly.newPlot('timeline', [
    { x: years, y: capability, mode: 'lines+markers', name: 'Disruption' }
  ], {
    title: 'Sector Disruption Timeline',
    xaxis: { title: 'Year' },
    yaxis: { title: 'Energy Remaining' }
  });

  Plotly.newPlot("pareto", [{
    x: population.map(p => p.effectiveness),
    y: population.map(p => p.risk),
    text: population.map(p => `Rank ${p.rank}`),
    mode: "markers",
    marker: { size: 12, color: population.map(p => p.rank) }
  }], {
    title: "Pareto Frontier",
    xaxis: { title: "Effectiveness" },
    yaxis: { title: "Risk" }
  });

  const logPanel = document.getElementById('logPanel');
  function addLog(msg) {
    const div = document.createElement('div');
    div.textContent = msg;
    logPanel.appendChild(div);
    logPanel.scrollTop = logPanel.scrollHeight;
  }
  ['Simulation started', 'Year 1: minor disruption', 'Year 3: new breakthrough'].forEach(addLog);
}

window.addEventListener('load', loadData);
