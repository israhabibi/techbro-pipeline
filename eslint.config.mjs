import globals from "globals";

export default [
  {
    files: ["src/**/*.mjs", "tests/**/*.mjs"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.node,
    },
    rules: {
      "no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", caughtErrorsIgnorePattern: "^_" },
      ],
      "no-undef": "error",
      "no-unreachable": "error",
      "no-constant-condition": "error",
    },
  },
];
