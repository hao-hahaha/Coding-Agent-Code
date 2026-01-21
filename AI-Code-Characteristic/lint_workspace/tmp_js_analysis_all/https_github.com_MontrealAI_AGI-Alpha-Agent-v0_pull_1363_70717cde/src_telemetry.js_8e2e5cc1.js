// SPDX-License-Identifier: Apache-2.0
/**
 * Lightweight telemetry helper.
 * Prompts for user consent and sends anonymous metrics to the OTLP endpoint.
 */

export function initTelemetry() {
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
    const allow = window.confirm('Allow anonymous telemetry?');
    consent = allow ? 'true' : 'false';
    localStorage.setItem(consentKey, consent);
  }

  const enabled = consent === 'true';
  const metrics = { ts: Date.now(), generations: 0, shares: 0 };

  function flush() {
    if (!enabled) return;
    navigator.sendBeacon(endpoint, JSON.stringify(metrics));
  }
  window.addEventListener('beforeunload', flush);

  return {
    recordRun(n) {
      if (enabled) metrics.generations += n;
    },
    recordShare() {
      if (enabled) metrics.shares += 1;
    },
  };
}
