import { test, expect } from "@playwright/test";

test("home shows theme buttons", async ({ page }) => {
  await page.goto("/");
  const buttons = page.getByRole("button", { name: /Adventure|Serene|Focus/ });
  await expect(buttons).toHaveCount(3);
});
