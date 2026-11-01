import { defineConfig, devices } from "@playwright/test";

/**
 * Browser E2E against REAL services: Next.js + FastAPI + a Supabase project dedicated to testing.
 * Required env: E2E_BASE_URL (default http://localhost:3000). See docs/TESTING_GUIDE.md.
 * The Supabase test project must have email confirmation disabled so sign-up yields a session.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
