"use client";

import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";
import { z } from "zod";

import { Field } from "@/components/shared/field";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { browserTimeZone, supportedTimeZones } from "@/features/events/datetime";
import { profileApi } from "@/features/events/api";
import { ApiError, userMessage } from "@/lib/api/errors";
import type { MetaDto, ProfileDto } from "@/types/api";

const schema = z.object({
  display_name: z.string().trim().min(1, "Enter your name.").max(80, "Use 80 characters or fewer."),
});

export function ProfileForm({ profile, meta }: { profile: ProfileDto; meta: MetaDto }) {
  const router = useRouter();
  const [name, setName] = React.useState(profile.display_name ?? "");
  const [locale, setLocale] = React.useState(profile.preferred_locale);
  const [tz, setTz] = React.useState(profile.timezone ?? browserTimeZone() ?? meta.default_timezone);
  const [error, setError] = React.useState<string>();
  const [busy, setBusy] = React.useState(false);
  const zones = React.useMemo(() => supportedTimeZones([meta.default_timezone, tz]), [meta.default_timezone, tz]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = schema.safeParse({ display_name: name });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message);
      return;
    }
    setError(undefined);
    setBusy(true);
    try {
      await profileApi.update({ display_name: parsed.data.display_name, preferred_locale: locale, timezone: tz });
      toast.success("Profile saved.");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError && err.fieldErrors.display_name) setError(err.fieldErrors.display_name);
      toast.error(userMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5" aria-label="Profile">
      <Field id="email" label="Email" hint="Your sign-in email is managed by your account.">
        {(a) => <Input {...a} value={profile.email ?? ""} readOnly disabled />}
      </Field>
      <Field id="display_name" label="Display name" error={error} required>
        {(a) => <Input {...a} value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />}
      </Field>
      <Field id="locale" label="Language and region">
        {(a) => (
          <Select {...a} value={locale} onChange={(e) => setLocale(e.target.value)}>
            {meta.locales.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <Field id="timezone" label="Preferred time zone">
        {(a) => (
          <Select {...a} value={tz} onChange={(e) => setTz(e.target.value)}>
            {zones.map((z) => (
              <option key={z} value={z}>
                {z.replaceAll("_", " ")}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <Button type="submit" loading={busy}>
        {busy ? "Saving" : "Save profile"}
      </Button>
    </form>
  );
}
