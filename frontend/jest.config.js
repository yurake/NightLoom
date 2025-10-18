const path = require("path");
const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
  tsconfig: "./tests/tsconfig.json",
});

const esmPackages = [
  "until-async",
  "@bundled-es-modules",
  "@inquirer",
  "chalk",
  "ansi-styles",
  "wrap-ansi",
  "string-width",
  "strip-ansi",
  "ansi-regex",
  "msw",
  "@mswjs/interceptors",
  "@mswjs/cookies",
  "outvariant",
  "strict-event-emitter",
];

const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&");
const esmPackagesPattern = esmPackages
  .map((pkg) => pkg.split("/").map(escapeRegex).join("\\/"))
  .join("|");
const esmTransformPattern = `node_modules/(?!(\\.pnpm/(?:[^/]+/)*(?:${esmPackagesPattern})|(?:${esmPackagesPattern})))`;

// MSW v2対応: 動的モジュール解決
let mswNodeEntry;
try {
  const mswPackageDir = path.dirname(require.resolve("msw/package.json"));
  mswNodeEntry = path.join(mswPackageDir, "lib/node/index.js");
} catch (error) {
  // Fallback for MSW v2
  mswNodeEntry = "msw/node";
}

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
    "^@/components/(.*)$": "<rootDir>/app/(play)/components/$1",
    "^@/types/(.*)$": "<rootDir>/app/types/$1",
    "^msw/node$": mswNodeEntry,
    // MSW v2互換性のための追加マッピング - より柔軟なマッピング
    "^@mswjs/interceptors/ClientRequest$": require.resolve("@mswjs/interceptors"),
    "^@mswjs/interceptors/(.*)$": require.resolve("@mswjs/interceptors"),
    "^@mswjs/cookies$": require.resolve("@mswjs/cookies"),
  },
  testPathIgnorePatterns: ["<rootDir>/e2e/"],
  // MSW対応: ESModules変換設定 - より包括的な設定
  transformIgnorePatterns: [esmTransformPattern],
};

module.exports = async () => {
  const config = await createJestConfig(customJestConfig)();

  // Jestのデフォルト`/node_modules/`設定を除外してESM依存関係を変換対象に含める
  config.transformIgnorePatterns = config.transformIgnorePatterns.filter(
    (pattern) => pattern !== "/node_modules/"
  );

  if (!config.transformIgnorePatterns.includes(esmTransformPattern)) {
    config.transformIgnorePatterns.push(esmTransformPattern);
  }

  return config;
};
