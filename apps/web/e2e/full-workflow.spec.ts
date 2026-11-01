import { expect, test, type Page } from "@playwright/test";

/**
 * Phase 1 acceptance scenario (P1-19, P1-17). Uses synthetic accounts only; each run
 * generates unique addresses on a reserved test domain. Requires a dedicated Supabase
 * TEST project (never production) with email confirmation disabled.
 */
const run = Date.now().toString(36);
const password = `Test-${run}-Aa1`; // generated per run, never reused or committed
const userA = { name: "Synthetic User A", email: `e2e-a-${run}@example.test` };
const userB = { name: "Synthetic User B", email: `e2e-b-${run}@example.test` };

async function register(page: Page, u: { name: string; email: string }) {
  await page.goto("/sign-up");
  await page.getByLabel("Your name").fill(u.name);
  await page.getByLabel("Email").fill(u.email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm password").fill(password);
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

async function signIn(page: Page, email: string) {
  await page.goto("/sign-in");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

async function signOut(page: Page) {
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/sign-in/);
}

test("two users: create, reopen, update, isolate", async ({ browser }) => {
  const ctxA = await browser.newContext();
  const a = await ctxA.newPage();

  // 1-3. A registers (and lands on the dashboard with a session)
  await register(a, userA);
  await expect(a.getByText("No events yet")).toBeVisible();

  // 3. A creates an event
  await a.getByRole("link", { name: "Create event" }).first().click();
  await a.getByLabel("Event title").fill("Synthetic Wedding A");
  await a.getByLabel("Starts").fill("2027-02-12T10:00");
  await a.getByLabel("Ends").fill("2027-02-14T22:00");
  await a.getByLabel("City").fill("Jaipur");
  await a.getByLabel("Expected guests").fill("300");
  await a.getByRole("button", { name: "Create event" }).click();
  await expect(a).toHaveURL(/\/events\/[0-9a-f-]{36}$/);
  const eventUrl = a.url();
  await expect(a.getByRole("heading", { level: 1, name: "Synthetic Wedding A" })).toBeVisible();

  // 5-6. Dashboard lists it; opening it works
  await a.goto("/dashboard");
  await expect(a.getByText("Synthetic Wedding A")).toBeVisible();
  await a.getByRole("link", { name: /Open Synthetic Wedding A/ }).click();

  // 7. Update
  await a.getByRole("button", { name: "Edit details" }).click();
  await a.getByLabel("Expected guests").fill("450");
  await a.getByRole("button", { name: "Save changes" }).click();
  await expect(a.getByText("450")).toBeVisible();

  // 8. Sign out, then sign in again and reopen (persistence)
  await signOut(a);
  await a.goto(eventUrl);
  await expect(a).toHaveURL(/\/sign-in/); // protected while signed out
  await signIn(a, userA.email);
  await a.goto(eventUrl);
  await expect(a.getByRole("heading", { level: 1, name: "Synthetic Wedding A" })).toBeVisible();

  // 9-12. B cannot see A's event; B creates and reopens their own
  const ctxB = await browser.newContext();
  const b = await ctxB.newPage();
  await register(b, userB);
  await b.goto(eventUrl);
  await expect(b.getByText("We could not find that page")).toBeVisible();
  await b.goto("/dashboard");
  await expect(b.getByText("Synthetic Wedding A")).toHaveCount(0);

  await b.getByRole("link", { name: "Create event" }).first().click();
  await b.getByLabel("Event title").fill("Synthetic Wedding B");
  await b.getByLabel("Starts").fill("2027-03-01T10:00");
  await b.getByLabel("Ends").fill("2027-03-01T20:00");
  await b.getByRole("button", { name: "Create event" }).click();
  await expect(b).toHaveURL(/\/events\/[0-9a-f-]{36}$/);
  const urlB = b.url();
  await b.goto("/dashboard");
  await b.getByRole("link", { name: /Open Synthetic Wedding B/ }).click();
  await expect(b).toHaveURL(urlB);

  await ctxA.close();
  await ctxB.close();
});
