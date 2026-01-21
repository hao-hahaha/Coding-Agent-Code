import js from "@eslint/js";
import sonarjs from "eslint-plugin-sonarjs";
import unicorn from "eslint-plugin-unicorn";
import importPlugin from "eslint-plugin-import";

export default [
  js.configs.recommended,

  {
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
    },

    plugins: {
      sonarjs,
      unicorn,
      import: importPlugin,
    },

    rules: {
      "sonarjs/cognitive-complexity": "warn",
    },
  },
];