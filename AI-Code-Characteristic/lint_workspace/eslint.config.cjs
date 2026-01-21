/**
 * ESLint v9 Flat Config (CommonJS)
 * - JS/JSX only
 * - Enables plugin rule sets when available
 */
const sonarjs = require("eslint-plugin-sonarjs");
const unicorn = require("eslint-plugin-unicorn");
const importPlugin = require("eslint-plugin-import");

function rulesFrom(plugin, configName) {
  try {
    const cfg = plugin && plugin.configs && plugin.configs[configName];
    return (cfg && cfg.rules) ? cfg.rules : {};
  } catch (e) {
    return {};
  }
}

module.exports = [
  {
    files: ["**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      sonarjs,
      unicorn,
      import: importPlugin,
    },
    rules: {
      // Plugin "recommended" rules (if present)
      ...rulesFrom(sonarjs, "recommended"),
      ...rulesFrom(unicorn, "recommended"),
      ...rulesFrom(importPlugin, "recommended"),

      // A few pragmatic defaults (optional; comment out if you want pure recommended-only)
      "no-unused-vars": "warn",
      "no-undef": "error",
    },
  },
];
