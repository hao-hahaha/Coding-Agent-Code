import React, { useEffect, useState } from 'react';

export default function Progress() {
  const [updates, setUpdates] = useState([]);

  useEffect(() => {
    const ws = new WebSocket(`ws://${location.host}/ws/progress`);
    ws.onmessage = ev => {
      try {
        const data = JSON.parse(ev.data);
        setUpdates(u => [...u, data]);
      } catch {
        // ignore malformed messages
      }
    };
    return () => ws.close();
  }, []);

  return (
    <div>
      <h2>Simulation Progress</h2>
      <ul>
        {updates.map(u => (
          <li key={u.year}>{u.year}: {u.capability}</li>
        ))}
      </ul>
    </div>
  );
}
