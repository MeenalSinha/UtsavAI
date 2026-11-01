"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { getServerEnv } from "@/config/env";
import { routes, safeNextPath } from "@/config/routes";
import {
  flattenErrors,
  forgotPasswordSchema,
  resetPasswordSchema,
  signInSchema,
  signUpSchema,
  type ActionState,
} from "@/features/auth/schemas";
import { createClient } from "@/lib/supabase/server";

async function siteOrigin(): Promise<string> {
  const h = await headers();
  const host = h.get("x-forwarded-host") ?? h.get("host");
  const proto = h.get("x-forwarded-proto") ?? (getServerEnv().NEXT_PUBLIC_APP_ENV === "production" ? "https" : "http");
  return `${proto}://${host}`;
}

function text(formData: FormData, key: string): string {
  const v = formData.get(key);
  return typeof v === "string" ? v : "";
}

export async function signInAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const parsed = signInSchema.safeParse({ email: text(formData, "email"), password: text(formData, "password") });
  if (!parsed.success) return { ok: false, fieldErrors: flattenErrors(parsed.error) };

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword(parsed.data);
  if (error) {
    // One generic message for wrong password/unknown user avoids account enumeration.
    const unconfirmed = error.code === "email_not_confirmed";
    return {
      ok: false,
      message: unconfirmed
        ? "Please confirm your email address first. Check your inbox for the verification link."
        : "The email or password is incorrect.",
    };
  }
  redirect(safeNextPath(text(formData, "next")));
}

export async function signUpAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const parsed = signUpSchema.safeParse({
    displayName: text(formData, "displayName"),
    email: text(formData, "email"),
    password: text(formData, "password"),
    confirmPassword: text(formData, "confirmPassword"),
  });
  if (!parsed.success) return { ok: false, fieldErrors: flattenErrors(parsed.error) };

  const supabase = await createClient();
  const origin = await siteOrigin();
  const { data, error } = await supabase.auth.signUp({
    email: parsed.data.email,
    password: parsed.data.password,
    options: {
      data: { display_name: parsed.data.displayName },
      emailRedirectTo: `${origin}${routes.authCallback}?next=${encodeURIComponent(routes.dashboard)}`,
    },
  });
  if (error) {
    if (error.code === "weak_password") return { ok: false, fieldErrors: { password: "Choose a stronger password." } };
    return { ok: false, message: "We could not create your account. Please try again." };
  }
  if (data.session) redirect(routes.dashboard); // email confirmation disabled in this project
  // Same response whether or not the address already exists (no enumeration).
  return { ok: true, message: "Check your email for a verification link to finish creating your account." };
}

export async function forgotPasswordAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const parsed = forgotPasswordSchema.safeParse({ email: text(formData, "email") });
  if (!parsed.success) return { ok: false, fieldErrors: flattenErrors(parsed.error) };

  const supabase = await createClient();
  const origin = await siteOrigin();
  await supabase.auth.resetPasswordForEmail(parsed.data.email, {
    redirectTo: `${origin}${routes.authCallback}?next=${encodeURIComponent(routes.resetPassword)}`,
  });
  return { ok: true, message: "If an account exists for that email, a password reset link is on its way." };
}

export async function resetPasswordAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const parsed = resetPasswordSchema.safeParse({
    password: text(formData, "password"),
    confirmPassword: text(formData, "confirmPassword"),
  });
  if (!parsed.success) return { ok: false, fieldErrors: flattenErrors(parsed.error) };

  const supabase = await createClient();
  const { data } = await supabase.auth.getUser();
  if (!data.user) return { ok: false, message: "Your reset link has expired. Request a new one." };
  const { error } = await supabase.auth.updateUser({ password: parsed.data.password });
  if (error) return { ok: false, message: "We could not update your password. Please request a new reset link." };
  redirect(`${routes.dashboard}`);
}

export async function signOutAction(): Promise<void> {
  const supabase = await createClient();
  await supabase.auth.signOut();
  redirect(routes.signIn);
}
