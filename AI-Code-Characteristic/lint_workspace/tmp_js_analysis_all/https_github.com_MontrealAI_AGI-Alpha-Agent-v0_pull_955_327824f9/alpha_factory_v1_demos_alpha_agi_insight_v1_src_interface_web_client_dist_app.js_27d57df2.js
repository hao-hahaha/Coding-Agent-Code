(function () {
  const { useEffect } = React;
  function App() {
    useEffect(() => {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      const ws = new WebSocket(`${proto}://${location.host}/ws/progress`);
      ws.onmessage = (e) => console.log(e.data);
      return () => ws.close();
    }, []);
    return React.createElement('div', null, 'α‑AGI Insight Demo');
  }
  ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(App));
})();
