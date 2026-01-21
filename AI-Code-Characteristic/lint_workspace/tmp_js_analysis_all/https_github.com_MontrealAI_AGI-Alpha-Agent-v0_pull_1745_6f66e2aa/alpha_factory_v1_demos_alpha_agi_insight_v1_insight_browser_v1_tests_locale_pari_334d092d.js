// SPDX-License-Identifier: Apache-2.0
const fs = require('fs');
const path = require('path');

const en = require('../src/i18n/en.json');

const dir = path.join(__dirname, '../src/i18n');

test('all locale files share the same keys', () => {
  const baseKeys = Object.keys(en).sort();
  for (const file of fs.readdirSync(dir)) {
    if (file === 'en.json') continue;
    const data = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8'));
    const keys = Object.keys(data).sort();
    expect(keys).toEqual(baseKeys);
  }
});
