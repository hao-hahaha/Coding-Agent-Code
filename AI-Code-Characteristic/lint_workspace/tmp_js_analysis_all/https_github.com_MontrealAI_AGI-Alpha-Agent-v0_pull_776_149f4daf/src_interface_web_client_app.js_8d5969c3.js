const { useState, useEffect } = React;

function App() {
  const [simId, setSimId] = useState(null);
  const [logs, setLogs] = useState([]);
  const [capability, setCapability] = useState([]);
  const [years, setYears] = useState([]);
  const [pareto, setPareto] = useState([]);

  useEffect(() => {
    if (!simId) return;
    const ws = new WebSocket(`ws://${location.host}/ws/${simId}`);
    ws.onmessage = (ev) => setLogs((l) => [...l, ev.data]);

    const iv = setInterval(async () => {
      const res = await fetch(`/results/${simId}`);
      if (!res.ok) return;
      const data = await res.json();
      if (data.forecast) {
        setCapability(data.forecast.map((p) => p.capability));
        setYears(data.forecast.map((p) => p.year));
      }
      if (data.pareto) {
        setPareto(data.pareto);
      }
      if (data.forecast) {
        clearInterval(iv);
        ws.close();
      }
    }, 1000);

    return () => {
      ws.close();
      clearInterval(iv);
    };
  }, [simId]);

  useEffect(() => {
    if (years.length) {
      const trace = { x: years, y: capability, type: 'scatter' };
      Plotly.react('cap-chart', [trace], { margin: { t: 20 } });
    }
  }, [years, capability]);

  useEffect(() => {
    if (pareto.length) {
      const trace = {
        x: pareto.map((p) => p[0]),
        y: pareto.map((p) => p[1]),
        mode: 'markers',
        type: 'scatter'
      };
      Plotly.react('pareto-chart', [trace], { margin: { t: 20 } });
    }
  }, [pareto]);

  async function start() {
    const res = await fetch('/simulate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    const data = await res.json();
    setLogs([]);
    setCapability([]);
    setPareto([]);
    setYears([]);
    setSimId(data.id);
  }

  return React.createElement('div', null,
    React.createElement('button', { onClick: start }, 'Run simulation'),
    React.createElement('div', { id: 'cap-chart', style: { width: '100%', height: '300px' } }),
    React.createElement('div', { id: 'pareto-chart', style: { width: '100%', height: '300px' } }),
    React.createElement('pre', null, logs.join('\n'))
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
