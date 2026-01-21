/* SPDX-License-Identifier: Apache-2.0 */
/* eslint-env browser */
/* global Chart */
/* eslint-disable no-undef */
import {setupPyodideDemo} from './pyodide_demo.js';

export async function replayChart({logsUrl, chartId = 'chart', logElId = 'logs-panel', label = 'Demo Metric', color = 'blue'}) {
  try {
    const res = await fetch(logsUrl);
    const data = await res.json();
    const ctx = document.getElementById(chartId);
    if (!ctx) return;
    const chart = new Chart(ctx, {
      type: 'line',
      data: { labels: [], datasets: [{ label, data: [], fill: false, borderColor: color }] },
      options: { animation: false, responsive: true, maintainAspectRatio: false }
    });
    const logEl = document.getElementById(logElId);
    setupPyodideDemo(chart, logEl, data);
  } catch (err) {
    console.error('replay failed', err);
  }
}
