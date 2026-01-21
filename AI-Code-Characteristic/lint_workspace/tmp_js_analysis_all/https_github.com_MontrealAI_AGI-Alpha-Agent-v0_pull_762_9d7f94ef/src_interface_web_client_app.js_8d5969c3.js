const { useState, useEffect } = React;

function App() {
  const [simId, setSimId] = useState(null);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (!simId) return;
    const ws = new WebSocket(`ws://${location.host}/ws/${simId}`);
    ws.onmessage = (ev) => setLogs((l) => [...l, ev.data]);
    return () => ws.close();
  }, [simId]);

  async function start() {
    const res = await fetch('/simulate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    const data = await res.json();
    setSimId(data.id);
    setLogs([]);
  }

  return React.createElement('div', null,
    React.createElement('button', { onClick: start }, 'Run simulation'),
    React.createElement('pre', null, logs.join('\n'))
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
