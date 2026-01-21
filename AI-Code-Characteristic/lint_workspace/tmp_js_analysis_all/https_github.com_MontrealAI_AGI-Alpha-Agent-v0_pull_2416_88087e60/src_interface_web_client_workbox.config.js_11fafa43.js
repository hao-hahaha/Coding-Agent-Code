// SPDX-License-Identifier: Apache-2.0
module.exports = {
  globDirectory: 'dist/',
  globPatterns: ['**/*.{js,css,html,wasm,woff2,svg,webmanifest,json}'],
  swSrc: 'src/sw.js',
  swDest: 'dist/service-worker.js',
  importWorkboxFrom: 'disabled',
};
