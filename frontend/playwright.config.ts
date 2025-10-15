import { defineConfig } from "@playwright/test";

export default defineConfig({
  webServer: {
    command: "pnpm dev",
    url: "http://localhost:3000",
    timeout: 120_000,
    reuseExistingServer: !process.env.CI,
  },
  testDir: "./e2e",
  use: {
    baseURL: "http://localhost:3000",
    // headless: false, // ブラウザを表示 (デバッグ用)
  },
  reporter: [["list"], ["html", { open: "never" }]],
});
