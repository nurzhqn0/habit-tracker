import { expect, test } from "@playwright/test";

// Full happy path against a real backend (TEST_MODE=1 enables the dev login).
test("login → create habit → toggle days → charts → room → leaderboard", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Make consistency visible." })).toBeVisible();

  // Dev login (bot username unset in e2e, so the fallback button renders).
  await page.getByRole("button", { name: /Dev login/ }).click();
  await page.waitForURL("**/app");

  // Create a habit.
  await page.getByRole("button", { name: "New habit" }).click();
  await page.getByPlaceholder("e.g. Meditate").fill("Read a book");
  await page.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page.getByText("Read a book")).toBeVisible();

  // Toggle today + 2 previous days in the grid (days render newest-first).
  const row = page.getByTestId("habit-row").first();
  const cells = row.getByTestId("check-cell");
  for (let offset = 0; offset < 3; offset++) {
    await cells.nth(offset).click();
    await page.waitForTimeout(300);
  }

  // Streak badge appears after 3 consecutive days.
  await expect(row.getByText("3 days")).toBeVisible();

  // Detail page renders chart cards.
  await page.getByText("Read a book", { exact: true }).click();
  await page.waitForURL("**/app/habits/**");
  await expect(page.getByText("Score", { exact: true })).toBeVisible();
  await expect(page.getByText("History", { exact: true })).toBeVisible();
  await expect(page.getByText("Best streaks")).toBeVisible();
  await expect(page.getByText("current streak")).toBeVisible();

  // Rooms: create, add a room habit, link own habit, check leaderboard.
  await page.goto("/app/rooms");
  await page.getByRole("button", { name: "New room" }).click();
  await page.getByPlaceholder("e.g. Morning Crew").fill("Book Club");
  await page.getByRole("button", { name: "Create", exact: true }).click();
  await page.waitForURL("**/app/rooms/**");

  await page.getByRole("button", { name: "Add room habit" }).click();
  await page.locator("form input").first().fill("Daily reading");
  await page.getByRole("button", { name: "Add", exact: true }).click();
  await expect(page.getByText("Daily reading")).toBeVisible();

  await page.getByRole("button", { name: "Link my habit" }).click();
  await page.getByRole("button", { name: "Read a book" }).click();
  await expect(page.getByRole("link", { name: "My habit" })).toBeVisible();

  await page.getByRole("tab", { name: "Leaderboard" }).click();
  await expect(page.getByText("(you)")).toBeVisible();
  await expect(page.getByText("1 linked habits")).toBeVisible();
});
