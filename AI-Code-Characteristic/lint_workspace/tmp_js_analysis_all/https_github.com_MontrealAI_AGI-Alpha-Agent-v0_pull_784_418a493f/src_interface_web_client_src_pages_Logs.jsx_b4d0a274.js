import React, { useEffect, useState } from 'react';

export default function Logs() {
  const [lines, setLines] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://${location.host}/ws/latest`);
    ws.onmessage = ev => setLines(l => [...l, ev.data]);
    return () => ws.close();
  }, []);

  return (
    <div>
      <h2>Live Logs</h2>
      <pre>{lines.join('\n')}</pre>
    </div>
  );
}
