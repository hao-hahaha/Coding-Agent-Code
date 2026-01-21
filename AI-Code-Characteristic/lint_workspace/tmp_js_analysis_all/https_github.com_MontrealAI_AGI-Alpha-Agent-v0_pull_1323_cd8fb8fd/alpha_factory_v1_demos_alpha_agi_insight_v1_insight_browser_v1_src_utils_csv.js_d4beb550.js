// SPDX-License-Identifier: Apache-2.0
export function toCSV(rows, headers) {
  if (!rows.length) return '';
  const keys = headers || Object.keys(rows[0]);
  const escape = (v) => `"${String(v).replace(/"/g, '""')}"`;
  const lines = [keys.join(',')];
  for (const row of rows) {
    lines.push(keys.map((k) => escape(row[k])).join(','));
  }
  return lines.join('\n');
}
