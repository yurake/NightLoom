import { test, expect } from "@playwright/test";

test("home shows theme buttons", async ({ page }) => {
  await page.goto("/");
  const expectedLabels = ["Adventure", "Serene", "Focus", "Fallback"];
  const buttons = page.getByRole("button", {
    name: new RegExp(expectedLabels.join("|")),
  });
  await expect(buttons).toHaveCount(expectedLabels.length);
  for (const label of expectedLabels) {
    await expect(page.getByRole("button", { name: label })).toBeVisible();
  }
});
