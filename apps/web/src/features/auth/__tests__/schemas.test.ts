import { describe, expect, it } from "vitest";

import { flattenErrors, forgotPasswordSchema, resetPasswordSchema, signInSchema, signUpSchema } from "@/features/auth/schemas";

function errs(result: { success: boolean; error?: import("zod").ZodError }) {
  if (result.success || !result.error) throw new Error("expected validation to fail");
  return flattenErrors(result.error);
}

describe("auth form schemas", () => {
  it("sign-in requires a valid email and a password", () => {
    expect(signInSchema.safeParse({ email: "a@example.com", password: "x" }).success).toBe(true);
    const r = signInSchema.safeParse({ email: "nope", password: "" });
    expect(r.success).toBe(false);
    if (!r.success) {
      const e = flattenErrors(r.error);
      expect(e.email).toMatch(/valid email/);
      expect(e.password).toMatch(/password/i);
    }
  });

  it("sign-up enforces password strength and confirmation", () => {
    const base = { displayName: "Asha", email: "asha@example.com", password: "abcdefg1", confirmPassword: "abcdefg1" };
    expect(signUpSchema.safeParse(base).success).toBe(true);
    expect(errs(signUpSchema.safeParse({ ...base, password: "short1", confirmPassword: "short1" })).password).toMatch(/8 characters/);
    expect(errs(signUpSchema.safeParse({ ...base, password: "onlyletters", confirmPassword: "onlyletters" })).password).toMatch(/letter and one number/);
    expect(errs(signUpSchema.safeParse({ ...base, confirmPassword: "different1" })).confirmPassword).toMatch(/do not match/);
    expect(signUpSchema.safeParse({ ...base, displayName: " " }).success).toBe(false);
  });

  it("forgot and reset password schemas", () => {
    expect(forgotPasswordSchema.safeParse({ email: "a@example.com" }).success).toBe(true);
    expect(forgotPasswordSchema.safeParse({ email: "" }).success).toBe(false);
    expect(resetPasswordSchema.safeParse({ password: "abcdefg1", confirmPassword: "abcdefg2" }).success).toBe(false);
  });
});
