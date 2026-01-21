// SPDX-License-Identifier: Apache-2.0
import daisyui from 'daisyui';

/** @type {import('tailwindcss').Config} */
export default {
  mode: 'jit',
  content: ['./index.html', './src/**/*.{js,ts}'],
  plugins: [daisyui]
};
