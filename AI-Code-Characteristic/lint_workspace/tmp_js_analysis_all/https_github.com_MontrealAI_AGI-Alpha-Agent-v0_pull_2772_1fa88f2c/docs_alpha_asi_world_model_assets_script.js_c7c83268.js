(() => {
  fetch('assets/logs.json')
    .then(res => res.json())
    .then(data => {
      const steps = data.steps || [];
      const values = data.values || [];
      const logs = data.logs || steps.map(s => `Step ${s}`);
      const ctx = document.getElementById('chart');
      if (!ctx) return;
      const chart = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Demo Metric', data: [], fill: false, borderColor: 'blue' }] },
        options: { animation: false, responsive: true, maintainAspectRatio: false }
      });
      let i = 0;
      const logEl = document.getElementById('logs-panel');
      function step() {
        if (i >= steps.length) return;
        chart.data.labels.push(steps[i]);
        chart.data.datasets[0].data.push(values[i]);
        chart.update();
        if (logEl) logEl.textContent += logs[i] + '\n';
        i += 1;
        setTimeout(step, 800);
      }
      step();
    })
    .catch(err => console.error('replay failed', err));
})();
