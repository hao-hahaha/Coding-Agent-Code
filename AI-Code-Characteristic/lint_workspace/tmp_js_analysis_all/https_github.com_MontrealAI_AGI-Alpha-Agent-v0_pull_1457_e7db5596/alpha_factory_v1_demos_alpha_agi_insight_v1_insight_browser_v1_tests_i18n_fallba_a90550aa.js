// SPDX-License-Identifier: Apache-2.0
const { initI18n, t } = require('../src/ui/i18n.js');

beforeEach(() => {
  global.fetch = jest.fn(() => Promise.reject(new Error('fail')));
});

test('fallback to english on fetch failure', async () => {
  await initI18n();
  expect(t('seed')).toBe('Seed');
});
