const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testEnvironment: "jest-environment-jsdom",
  testEnvironmentOptions: {
    // MSW対応: jsdom環境でのURL設定
    url: "http://localhost:3000",
    // React 18 compatibility: enable concurrent features in test environment
    resources: "usable",
    runScripts: "dangerously",
  },
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/app/$1",
  },
  testPathIgnorePatterns: ['<rootDir>/e2e/'],
  // MSW対応: ESModules変換設定 - より包括的な設定
  transformIgnorePatterns: [
    "node_modules/(?!(.pnpm|msw|@mswjs|until-async|@bundled-es-modules|@inquirer|chalk|ansi-styles|wrap-ansi|string-width|strip-ansi|ansi-regex))"
  ],
};

module.exports = createJestConfig(customJestConfig);
