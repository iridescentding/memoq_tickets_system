import globals from "globals";
import pluginJs from "@eslint/js";
import pluginVue from "eslint-plugin-vue";

export default [
  { languageOptions: { globals: globals.browser } },
  pluginJs.configs.recommended,
  ...pluginVue.configs['flat/recommended'], // Changed from flat/essential to flat/recommended for Vue 3
  {
    files: ["**/*.vue"],
    languageOptions: {
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      }
    },
    rules: {
      "vue/multi-word-component-names": "off",
      "vue/no-unused-vars": "warn",
      // If 'vue/valid-v-slot' errors persist for correct syntax, consider targeted adjustments or, as a last resort, disabling for specific lines/blocks if it's a linter bug with complex slot names.
    }
  },
  {
    // Ignoring eslint.config.js itself if it's within the linted paths, though typically it's at project root.
    // node_modules and dist are standard ignores.
    ignores: ["dist/**", "node_modules/**"]
  }
];

