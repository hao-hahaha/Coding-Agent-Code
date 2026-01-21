/* SPDX-License-Identifier: Apache-2.0 */
/* eslint-env browser */
/* global Chart */
/* eslint-disable no-undef */
import {setupPyodideDemo} from '../assets/pyodide_demo.js';

fetch('assets/logs.json')
  .then(res => res.json())
  .then(data => {
    // allow both {steps, values} and {timestamps, metrics}
    if (data.timestamps && !data.steps) data.steps = data.timestamps;
    if (data.metrics && !data.values) data.values = data.metrics;

    const ctx = document.getElementById('chart');
    if (!ctx) return;
    const chart = new Chart(ctx, {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'Demo Metric', data: [], fill: false, borderColor: 'blue' }] },
      options: { animation: false, responsive: true, maintainAspectRatio: false }
    });
    const logEl = document.getElementById('logs-panel');
    setupPyodideDemo(chart, logEl, data);
  })
  .catch(err => console.error('replay failed', err));
