import { describe, expect, it } from "vitest";

import { ConfigError, parsePublicEnv, parseServerEnv } from "@/config/env";
import { isAuthOnlyPath, isProtectedPath, safeNextPath } from "@/config/routes";
import { decideAccess } from "@/lib/supabase/middleware";

const base = {
  NEXT_PUBLIC_SUPABASE_URL: "https://abc.supabase.co",
  NEXT_PUBLIC_SUPABASE_ANON_KEY: "x".repeat(40),
  API_BASE_URL: "http://localhost:8000",
};

describe("environment validation", () => {
  it("accepts a complete configuration and applies defaults", () => {
    const env = parseServerEnv(base);
    expect(env.NEXT_PUBLIC_APP_ENV).toBe("development");
    expect(env.BACKEND_TIMEOUT_MS).toBe(15000);
  });

  it("fails clearly when required variables are missing", () => {
    expect(() => parseServerEnv({})).toThrow(ConfigError);
    expect(() => parseServerEnv({ ...base, API_BASE_URL: undefined })).toThrow(/API_BASE_URL/);
    expect(() => parsePublicEnv({ ...base, NEXT_PUBLIC_SUPABASE_URL: "nope" })).toThrow(/NEXT_PUBLIC_SUPABASE_URL/);
  });

  it("requires https in production", () => {
    expect(() => parseServerEnv({ ...base, NEXT_PUBLIC_APP_ENV: "production" })).toThrow(/https/);
    expect(
      parseServerEnv({ ...base, NEXT_PUBLIC_APP_ENV: "production", API_BASE_URL: "https://api.example.com" }).API_BASE_URL,
    ).toBe("https://api.example.com");
  });

  it("never lists the backend URL as browser-visible configuration", () => {
    expect(Object.keys(parsePublicEnv(base))).not.toContain("API_BASE_URL");
  });
});

describe("route protection", () => {
  it("protects dashboard, events and profile", () => {
    for (const p of ["/dashboard", "/events", "/events/new", "/events/123", "/profile"]) expect(isProtectedPath(p)).toBe(true);
    for (const p of ["/", "/sign-in", "/sign-up", "/eventsfoo", "/auth/callback"]) expect(isProtectedPath(p)).toBe(false);
  });

  it("identifies auth-only pages", () => {
    expect(isAuthOnlyPath("/sign-in")).toBe(true);
    expect(isAuthOnlyPath("/reset-password")).toBe(false);
  });

  it("redirects anonymous users to sign-in and remembers the destination", () => {
    expect(decideAccess("/events/abc", "?x=1", false)).toEqual({
      action: "redirect",
      to: "/sign-in?next=%2Fevents%2Fabc%3Fx%3D1",
    });
  });

  it("redirects signed-in users away from sign-in and allows everything else", () => {
    expect(decideAccess("/sign-in", "", true)).toEqual({ action: "redirect", to: "/dashboard" });
    expect(decideAccess("/dashboard", "", true)).toEqual({ action: "next" });
    expect(decideAccess("/", "", false)).toEqual({ action: "next" });
    expect(decideAccess("/reset-password", "", true)).toEqual({ action: "next" });
  });
});

describe("safeNextPath (open redirect protection)", () => {
  it("allows same-site relative paths", () => {
    expect(safeNextPath("/events/abc?tab=1")).toBe("/events/abc?tab=1");
  });
  it.each(["https://evil.example", "//evil.example", "/\\evil.example", "javascript:alert(1)", "", null, undefined])(
    "rejects %s",
    (value) => {
      expect(safeNextPath(value as string | null | undefined)).toBe("/dashboard");
    },
  );
});
