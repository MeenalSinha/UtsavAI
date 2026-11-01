import { z } from "zod";

import type { MetaDto } from "@/types/api";
import { isValidTimeZone, zonedLocalToUtcIso } from "@/features/events/datetime";

export const DATE_RANGE_MESSAGE = "The end must be on or after the start.";

export interface EventFormValues {
  title: string;
  event_type: string;
  start_local: string;
  end_local: string;
  timezone: string;
  location_name: string;
  city: string;
  region: string;
  country_code: string;
  expected_guest_count: string;
  currency: string;
}

/** Client-side validation for usability; the API remains the authority. */
export function buildEventFormSchema(meta: Pick<MetaDto, "currencies" | "event_types" | "limits">) {
  const titleMax = meta.limits.title_max ?? 160;
  const partMax = meta.limits.location_part_max ?? 120;
  const nameMax = meta.limits.location_name_max ?? 160;
  const guestMax = meta.limits.guest_count_max ?? 100000;
  const enabledTypes = meta.event_types.filter((t) => t.enabled).map((t) => t.key);

  return z
    .object({
      title: z.string().trim().min(1, "Give your event a title.").max(titleMax, `Use ${titleMax} characters or fewer.`),
      event_type: z.string().refine((v) => enabledTypes.includes(v), "Choose an available category."),
      start_local: z.string().min(1, "Choose a start date and time."),
      end_local: z.string().min(1, "Choose an end date and time."),
      timezone: z.string().refine(isValidTimeZone, "Choose a valid time zone."),
      location_name: z.string().trim().max(nameMax, `Use ${nameMax} characters or fewer.`),
      city: z.string().trim().max(partMax, `Use ${partMax} characters or fewer.`),
      region: z.string().trim().max(partMax, `Use ${partMax} characters or fewer.`),
      country_code: z.string().refine((v) => v === "" || /^[A-Z]{2}$/.test(v), "Choose a valid country."),
      expected_guest_count: z
        .string()
        .trim()
        .refine((v) => /^\d+$/.test(v), "Enter a whole number, 0 or more.")
        .refine((v) => Number(v) <= guestMax, `Guest count cannot exceed ${guestMax.toLocaleString("en-IN")}.`),
      currency: z.string().refine((v) => meta.currencies.includes(v), "Choose a supported currency."),
    })
    .superRefine((v, ctx) => {
      const start = zonedLocalToUtcIso(v.start_local, v.timezone);
      const end = zonedLocalToUtcIso(v.end_local, v.timezone);
      if (v.start_local && !start) ctx.addIssue({ code: "custom", path: ["start_local"], message: "Enter a valid start date." });
      if (v.end_local && !end) ctx.addIssue({ code: "custom", path: ["end_local"], message: "Enter a valid end date." });
      if (start && end && Date.parse(end) < Date.parse(start)) {
        ctx.addIssue({ code: "custom", path: ["end_local"], message: DATE_RANGE_MESSAGE });
      }
    });
}

export function toCreateBody(values: EventFormValues) {
  const blank = (s: string) => (s.trim() === "" ? null : s.trim());
  return {
    event_type: values.event_type,
    title: values.title.trim(),
    start_at: zonedLocalToUtcIso(values.start_local, values.timezone)!,
    end_at: zonedLocalToUtcIso(values.end_local, values.timezone)!,
    timezone: values.timezone,
    location: {
      name: blank(values.location_name),
      city: blank(values.city),
      region: blank(values.region),
      country_code: blank(values.country_code),
    },
    expected_guest_count: Number(values.expected_guest_count),
    currency: values.currency,
  };
}
