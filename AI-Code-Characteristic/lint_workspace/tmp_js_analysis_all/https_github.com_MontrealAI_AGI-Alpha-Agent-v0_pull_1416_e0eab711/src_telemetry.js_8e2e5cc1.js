// SPDX-License-Identifier: Apache-2.0
/**
 * Lightweight telemetry helper.
 * Prompts for user consent and sends anonymous metrics to the OTLP endpoint.
 */

export async function hashSession(id) {
  const buf = await crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode('insight' + id),
  );
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export function initTelemetry(t) {
  const endpoint =
    (typeof process !== 'undefined' && process.env.OTEL_ENDPOINT) ||
    (typeof window !== 'undefined' && window.OTEL_ENDPOINT) ||
    (typeof import.meta !== 'undefined' && import.meta.env.VITE_OTEL_ENDPOINT);

  if (!endpoint) {
    return { recordRun() {}, recordShare() {} };
  }

  const consentKey = 'telemetryConsent';
  let consent = localStorage.getItem(consentKey);
  if (consent === null) {
    const prompt = typeof t === 'function' ? t('telemetry_consent') : 'Allow anonymous telemetry?';
    const allow = window.confirm(prompt);
    consent = allow ? 'true' : 'false';
    localStorage.setItem(consentKey, consent);
  }

  const enabled = consent === 'true';
  const queueKey = 'telemetryQueue';
  const metrics = { ts: Date.now(), session: '', generations: 0, shares: 0 };
  const queue = JSON.parse(localStorage.getItem(queueKey) || '[]');

  const ready = (async () => {
    let sid = localStorage.getItem('telemetrySession');
    if (!sid) {
      sid = await hashSession(crypto.randomUUID());
      localStorage.setItem('telemetrySession', sid);
    }
    metrics.session = sid;
  })();

  async function sendQueue() {
    if (!enabled) return;
    await ready;
    while (queue.length && navigator.onLine) {
      const payload = queue[0];
      if (navigator.sendBeacon(endpoint, JSON.stringify(payload))) {
        queue.shift();
      } else {
        break;
      }
    }
    localStorage.setItem(queueKey, JSON.stringify(queue));
  }

  function flush() {
    if (!enabled) return;
    metrics.ts = Date.now();
    queue.push({ ...metrics });
    localStorage.setItem(queueKey, JSON.stringify(queue));
    void sendQueue();
  }
  window.addEventListener('beforeunload', flush);
  window.addEventListener('online', () => void sendQueue());
  void sendQueue();

  return {
    recordRun(n) {
      if (enabled) metrics.generations += n;
    },
    recordShare() {
      if (enabled) metrics.shares += 1;
    },
  };
}
