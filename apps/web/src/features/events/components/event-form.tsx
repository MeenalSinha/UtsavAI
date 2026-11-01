"use client";

import { useRouter } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { Field } from "@/components/shared/field";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { routes } from "@/config/routes";
import { eventsApi } from "@/features/events/api";
import { browserTimeZone, supportedTimeZones, utcIsoToZonedLocal } from "@/features/events/datetime";
import { buildEventFormSchema, toCreateBody, type EventFormValues } from "@/features/events/schemas";
import { ApiError, userMessage } from "@/lib/api/errors";
import type { EventDto, EventUpdateBody, MetaDto } from "@/types/api";

type Errors = Partial<Record<keyof EventFormValues | "form", string>>;

const API_FIELD_TO_FORM: Record<string, keyof EventFormValues> = {
  title: "title",
  start_at: "start_local",
  end_at: "end_local",
  timezone: "timezone",
  "location.name": "location_name",
  "location.city": "city",
  "location.region": "region",
  "location.country_code": "country_code",
  expected_guest_count: "expected_guest_count",
  currency: "currency",
  event_type: "event_type",
};

function initialValues(meta: MetaDto, event?: EventDto): EventFormValues {
  if (event) {
    return {
      title: event.title,
      event_type: event.event_type,
      start_local: utcIsoToZonedLocal(event.start_at, event.timezone),
      end_local: utcIsoToZonedLocal(event.end_at, event.timezone),
      timezone: event.timezone,
      location_name: event.location.name ?? "",
      city: event.location.city ?? "",
      region: event.location.region ?? "",
      country_code: event.location.country_code ?? "",
      expected_guest_count: String(event.expected_guest_count),
      currency: event.currency,
    };
  }
  return {
    title: "",
    event_type: meta.default_event_type,
    start_local: "",
    end_local: "",
    timezone: meta.default_timezone,
    location_name: "",
    city: "",
    region: "",
    country_code: meta.default_country_code,
    expected_guest_count: "0",
    currency: meta.default_currency,
  };
}

interface Props {
  meta: MetaDto;
  event?: EventDto;
  onSaved?: (event: EventDto) => void;
  onCancel?: () => void;
}

export function EventForm({ meta, event, onSaved, onCancel }: Props) {
  const router = useRouter();
  const editing = Boolean(event);
  const schema = React.useMemo(() => buildEventFormSchema(meta), [meta]);
  const [values, setValues] = React.useState<EventFormValues>(() => initialValues(meta, event));
  const [errors, setErrors] = React.useState<Errors>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [conflict, setConflict] = React.useState(false);

  const zones = React.useMemo(
    () => supportedTimeZones([meta.default_timezone, values.timezone, ...(browserTimeZone() ? [browserTimeZone()!] : [])]),
    [meta.default_timezone, values.timezone],
  );
  const regionNames = React.useMemo(() => {
    try {
      return new Intl.DisplayNames(["en"], { type: "region" });
    } catch {
      return null;
    }
  }, []);

  const set = (name: keyof EventFormValues) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setValues((v) => ({ ...v, [name]: e.target.value }));

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setConflict(false);
    const parsed = schema.safeParse(values);
    if (!parsed.success) {
      const next: Errors = {};
      for (const issue of parsed.error.issues) next[issue.path[0] as keyof EventFormValues] ??= issue.message;
      setErrors(next);
      const first = Object.keys(next)[0];
      if (first) document.getElementById(first)?.focus();
      return;
    }
    setErrors({});
    setSubmitting(true);
    try {
      const body = toCreateBody(values);
      if (editing && event) {
        const { event_type: _t, ...update } = body;
        const saved = await eventsApi.update(event.id, update as EventUpdateBody, event.revision);
        toast.success("Event updated.");
        onSaved?.(saved);
        router.refresh();
      } else {
        const created = await eventsApi.create(body);
        toast.success("Your event has been created.");
        router.push(routes.event(created.id));
        router.refresh();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isConflict) {
          setConflict(true);
        } else {
          const mapped: Errors = {};
          for (const [field, message] of Object.entries(err.fieldErrors)) {
            const key = API_FIELD_TO_FORM[field];
            if (key) mapped[key] ??= message;
          }
          setErrors(Object.keys(mapped).length ? mapped : { form: userMessage(err) });
        }
      } else {
        setErrors({ form: userMessage(err) });
      }
      toast.error(err instanceof ApiError && err.isConflict ? "This event changed elsewhere." : userMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-8" aria-label={editing ? "Edit event" : "Create event"}>
      {errors.form && <Alert tone="error">{errors.form}</Alert>}
      {conflict && (
        <Alert tone="error">
          This event was changed by someone else since you opened it.{" "}
          <button type="button" className="font-medium underline" onClick={() => router.refresh()}>
            Reload the latest version
          </button>{" "}
          and re-apply your edits.
        </Alert>
      )}

      <section className="grid gap-5 sm:grid-cols-2" aria-labelledby="basics">
        <h2 id="basics" className="sm:col-span-2 text-lg font-semibold">Basics</h2>
        <Field id="title" label="Event title" error={errors.title} required className="sm:col-span-2">
          {(a) => <Input {...a} value={values.title} onChange={set("title")} maxLength={meta.limits.title_max} placeholder="Aarav and Meera's Wedding" />}
        </Field>
        <Field id="event_type" label="Category" error={errors.event_type} required>
          {(a) => (
            <Select {...a} value={values.event_type} onChange={set("event_type")} disabled={editing}>
              {meta.event_types.map((t) => (
                <option key={t.key} value={t.key} disabled={!t.enabled}>
                  {t.label}
                  {t.enabled ? "" : " (coming soon)"}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field id="expected_guest_count" label="Expected guests" error={errors.expected_guest_count} required>
          {(a) => <Input {...a} type="number" inputMode="numeric" min={0} step={1} value={values.expected_guest_count} onChange={set("expected_guest_count")} />}
        </Field>
      </section>

      <section className="grid gap-5 sm:grid-cols-2" aria-labelledby="when">
        <h2 id="when" className="sm:col-span-2 text-lg font-semibold">When</h2>
        <Field id="start_local" label="Starts" error={errors.start_local} required>
          {(a) => <Input {...a} type="datetime-local" value={values.start_local} onChange={set("start_local")} />}
        </Field>
        <Field id="end_local" label="Ends" error={errors.end_local} required>
          {(a) => <Input {...a} type="datetime-local" value={values.end_local} onChange={set("end_local")} />}
        </Field>
        <Field id="timezone" label="Time zone" error={errors.timezone} hint="Dates are entered and shown in this time zone." required className="sm:col-span-2">
          {(a) => (
            <Select {...a} value={values.timezone} onChange={set("timezone")}>
              {zones.map((z) => (
                <option key={z} value={z}>
                  {z.replaceAll("_", " ")}
                </option>
              ))}
            </Select>
          )}
        </Field>
      </section>

      <section className="grid gap-5 sm:grid-cols-2" aria-labelledby="where">
        <h2 id="where" className="sm:col-span-2 text-lg font-semibold">Where</h2>
        <Field id="location_name" label="Venue or location" error={errors.location_name} className="sm:col-span-2">
          {(a) => <Input {...a} value={values.location_name} onChange={set("location_name")} />}
        </Field>
        <Field id="city" label="City" error={errors.city}>
          {(a) => <Input {...a} value={values.city} onChange={set("city")} autoComplete="address-level2" />}
        </Field>
        <Field id="region" label="State or region" error={errors.region}>
          {(a) => <Input {...a} value={values.region} onChange={set("region")} autoComplete="address-level1" />}
        </Field>
        <Field id="country_code" label="Country" error={errors.country_code}>
          {(a) => (
            <Select {...a} value={values.country_code} onChange={set("country_code")}>
              <option value="">Not specified</option>
              {meta.suggested_country_codes.map((c) => (
                <option key={c} value={c}>
                  {regionNames?.of(c) ?? c}
                </option>
              ))}
            </Select>
          )}
        </Field>
        <Field id="currency" label="Currency" error={errors.currency} required>
          {(a) => (
            <Select {...a} value={values.currency} onChange={set("currency")}>
              {meta.currencies.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
          )}
        </Field>
      </section>

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={submitting}>
            Cancel
          </Button>
        )}
        <Button type="submit" loading={submitting}>
          {submitting ? "Saving" : editing ? "Save changes" : "Create event"}
        </Button>
      </div>
    </form>
  );
}
