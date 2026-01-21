// SPDX-License-Identifier: Apache-2.0
/*
 * Simple debate arena executed in a Web Worker. The worker receives a
 * hypothesis string and runs a fixed exchange between four roles:
 * Proposer, Skeptic, Regulator and Investor. The outcome score is
 * returned to the caller along with the threaded messages.
 */
self.onmessage = (ev) => {
  const { hypothesis } = ev.data || {};
  if (!hypothesis) return;

  const messages = [
    { role: 'Proposer', text: `I propose that ${hypothesis}.` },
    { role: 'Skeptic', text: `I doubt that ${hypothesis} holds under scrutiny.` },
    { role: 'Regulator', text: `Any implementation of ${hypothesis} must be safe.` },
  ];

  const approved = Math.random() > 0.5;
  messages.push({
    role: 'Investor',
    text: approved
      ? `Funding approved for: ${hypothesis}.`
      : `Funding denied for: ${hypothesis}.`,
  });

  const score = approved ? 1 : 0;
  self.postMessage({ messages, score });
};
