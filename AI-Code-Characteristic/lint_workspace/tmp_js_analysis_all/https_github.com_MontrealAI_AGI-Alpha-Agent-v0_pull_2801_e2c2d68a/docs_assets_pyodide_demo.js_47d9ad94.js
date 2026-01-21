/* SPDX-License-Identifier: Apache-2.0 */
/* eslint-env browser */
/* eslint-disable no-undef */
import {loadPyodide} from '../assets/pyodide/pyodide.js';

export function setupPyodideDemo(chart, logEl, defaultData) {
  function showMessage(msg) {
    if (logEl) {
      logEl.textContent += `${msg}\n`;
    }
  }

  function render(data) {
    const steps = data.steps || [];
    const values = data.values || [];
    const logs = data.logs || [];
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    if (logEl) logEl.textContent = '';
    steps.forEach((s, idx) => {
      chart.data.labels.push(s);
      chart.data.datasets[0].data.push(values[idx]);
      chart.update();
      if (logEl && logs[idx]) logEl.textContent += logs[idx] + '\n';
    });
  }

  render(defaultData);

  let pyodide;
  const offlineBtn = document.getElementById('offline-mode');
  const onlineBtn = document.getElementById('online-mode');

  offlineBtn?.addEventListener('click', async () => {
    if (!pyodide) {
      showMessage('Loading Python runtime...');
      pyodide = await loadPyodide();
    }
    const code = `import json, random
steps = list(range(1, 11))
values = [random.random() for _ in steps]
logs = [f"offline step {i}" for i in steps]
json.dumps({"steps": steps, "values": values, "logs": logs})`;
    const result = await pyodide.runPythonAsync(code);
    render(JSON.parse(result));
    showMessage('Offline simulation complete.');
  });

  onlineBtn?.addEventListener('click', async () => {
    const key = window.prompt('Enter OpenAI API key');
    if (!key) return;
    showMessage('Querying OpenAI API...');
    try {
      const resp = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${key}`,
        },
        body: JSON.stringify({
          model: 'gpt-3.5-turbo',
          messages: [{
            role: 'user',
            content: 'Return JSON {"steps": [1,2,...,10], "values": [10 floats], "logs": [10 strings]}'
          }],
        }),
      });
      const data = await resp.json();
      const text = data.choices?.[0]?.message?.content || '{}';
      let parsed = {};
      try {
        parsed = JSON.parse(text);
      } catch (e) {
        console.error('OpenAI response parse error', e);
      }
      render(parsed);
      showMessage('OpenAI response received.');
    } catch (err) {
      console.error('OpenAI request failed', err);
      showMessage('OpenAI request failed. See console for details.');
    }
  });
}
