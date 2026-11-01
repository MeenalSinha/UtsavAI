"use client";

import Link from "next/link";
import * as React from "react";
import { useActionState } from "react";

import { Field } from "@/components/shared/field";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { routes } from "@/config/routes";
import {
  forgotPasswordAction,
  resetPasswordAction,
  signInAction,
  signUpAction,
} from "@/features/auth/actions";
import {
  flattenErrors,
  forgotPasswordSchema,
  resetPasswordSchema,
  signInSchema,
  signUpSchema,
  type ActionState,
} from "@/features/auth/schemas";
import type { z } from "zod";

type ServerAction = (prev: ActionState, formData: FormData) => Promise<ActionState>;

const initial: ActionState = { ok: false };

/**
 * Client-side validation runs first for usability. The server action validates again
 * and remains the authority; Supabase enforces the real account rules.
 */
function useValidatedAction(action: ServerAction, schema: z.ZodTypeAny, fields: string[]) {
  const [state, formAction, pending] = useActionState(action, initial);
  const [clientErrors, setClientErrors] = React.useState<Record<string, string>>({});

  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    const data = new FormData(event.currentTarget);
    const values = Object.fromEntries(fields.map((f) => [f, String(data.get(f) ?? "")]));
    const result = schema.safeParse(values);
    if (!result.success) {
      event.preventDefault();
      setClientErrors(flattenErrors(result.error));
      return;
    }
    setClientErrors({});
  };

  const errors = { ...(state.fieldErrors ?? {}), ...clientErrors };
  return { state, formAction, pending, onSubmit, errors };
}

export function SignInForm({ next, notice }: { next?: string; notice?: string }) {
  const { state, formAction, pending, onSubmit, errors } = useValidatedAction(signInAction, signInSchema, ["email", "password"]);
  return (
    <form action={formAction} onSubmit={onSubmit} noValidate className="space-y-4" aria-label="Sign in">
      {notice && <Alert tone="info">{notice}</Alert>}
      {state.message && !state.ok && <Alert tone="error">{state.message}</Alert>}
      <input type="hidden" name="next" value={next ?? ""} />
      <Field id="email" label="Email" error={errors.email} required>
        {(a) => <Input {...a} name="email" type="email" autoComplete="email" inputMode="email" />}
      </Field>
      <Field id="password" label="Password" error={errors.password} required>
        {(a) => <Input {...a} name="password" type="password" autoComplete="current-password" />}
      </Field>
      <div className="flex justify-end">
        <Link href={routes.forgotPassword} className="text-sm text-primary hover:underline">
          Forgot password?
        </Link>
      </div>
      <Button type="submit" className="w-full" loading={pending}>
        {pending ? "Signing in" : "Sign in"}
      </Button>
    </form>
  );
}

export function SignUpForm() {
  const { state, formAction, pending, onSubmit, errors } = useValidatedAction(signUpAction, signUpSchema, [
    "displayName",
    "email",
    "password",
    "confirmPassword",
  ]);
  if (state.ok) return <Alert tone="success">{state.message}</Alert>;
  return (
    <form action={formAction} onSubmit={onSubmit} noValidate className="space-y-4" aria-label="Create account">
      {state.message && <Alert tone="error">{state.message}</Alert>}
      <Field id="displayName" label="Your name" error={errors.displayName} required>
        {(a) => <Input {...a} name="displayName" autoComplete="name" />}
      </Field>
      <Field id="email" label="Email" error={errors.email} required>
        {(a) => <Input {...a} name="email" type="email" autoComplete="email" inputMode="email" />}
      </Field>
      <Field id="password" label="Password" error={errors.password} hint="At least 8 characters with a letter and a number." required>
        {(a) => <Input {...a} name="password" type="password" autoComplete="new-password" />}
      </Field>
      <Field id="confirmPassword" label="Confirm password" error={errors.confirmPassword} required>
        {(a) => <Input {...a} name="confirmPassword" type="password" autoComplete="new-password" />}
      </Field>
      <Button type="submit" className="w-full" loading={pending}>
        {pending ? "Creating account" : "Create account"}
      </Button>
    </form>
  );
}

export function ForgotPasswordForm() {
  const { state, formAction, pending, onSubmit, errors } = useValidatedAction(forgotPasswordAction, forgotPasswordSchema, ["email"]);
  if (state.ok) return <Alert tone="success">{state.message}</Alert>;
  return (
    <form action={formAction} onSubmit={onSubmit} noValidate className="space-y-4" aria-label="Reset password">
      {state.message && <Alert tone="error">{state.message}</Alert>}
      <Field id="email" label="Email" error={errors.email} required>
        {(a) => <Input {...a} name="email" type="email" autoComplete="email" inputMode="email" />}
      </Field>
      <Button type="submit" className="w-full" loading={pending}>
        {pending ? "Sending link" : "Send reset link"}
      </Button>
    </form>
  );
}

export function ResetPasswordForm() {
  const { state, formAction, pending, onSubmit, errors } = useValidatedAction(resetPasswordAction, resetPasswordSchema, [
    "password",
    "confirmPassword",
  ]);
  return (
    <form action={formAction} onSubmit={onSubmit} noValidate className="space-y-4" aria-label="Choose a new password">
      {state.message && <Alert tone="error">{state.message}</Alert>}
      <Field id="password" label="New password" error={errors.password} required>
        {(a) => <Input {...a} name="password" type="password" autoComplete="new-password" />}
      </Field>
      <Field id="confirmPassword" label="Confirm new password" error={errors.confirmPassword} required>
        {(a) => <Input {...a} name="confirmPassword" type="password" autoComplete="new-password" />}
      </Field>
      <Button type="submit" className="w-full" loading={pending}>
        {pending ? "Saving" : "Update password"}
      </Button>
    </form>
  );
}
