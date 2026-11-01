import { describe, expect, it } from "vitest";

import { buildEventFormSchema, toCreateBody, type EventFormValues } from "@/features/events/schemas";
import { meta } from "@/test/fixtures";


const valid: EventFormValues = {
  title: "My Wedding",
  event_type: "wedding",
  start_local: "2027-02-12T10:00",
  end_local: "2027-02-14T22:00",
  timezone: "Asia/Kolkata",
  location_name: "Jaipur",
  city: "Jaipur",
  region: "Rajasthan",
  country_code: "IN",
  expected_guest_count: "300",
  currency: "INR",
};

const schema = buildEventFormSchema(meta);
const errorsFor = (patch: Partial<EventFormValues>) => {
  const r = schema.safeParse({ ...valid, ...patch });
  return r.success ? {} : Object.fromEntries(r.error.issues.map((i) => [String(i.path[0]), i.message]));
};

describe("event form validation", () => {
  it("accepts a valid event", () => {
    expect(schema.safeParse(valid).success).toBe(true);
  });

  it("requires title, start and end", () => {
    const e = errorsFor({ title: "  ", start_local: "", end_local: "" });
    expect(e.title).toMatch(/title/i);
    expect(e.start_local).toBeDefined();
    expect(e.end_local).toBeDefined();
  });

  it("prevents an end before the start", () => {
    expect(errorsFor({ end_local: "2027-02-11T10:00" }).end_local).toMatch(/on or after/);
  });

  it("allows equal start and end", () => {
    expect(errorsFor({ end_local: "2027-02-12T10:00" })).toEqual({});
  });

  it.each(["-1", "1.5", "abc", ""])("rejects guest count %j", (value) => {
    expect(errorsFor({ expected_guest_count: value }).expected_guest_count).toBeDefined();
  });

  it("accepts a guest count of zero and rejects over the limit", () => {
    expect(errorsFor({ expected_guest_count: "0" })).toEqual({});
    expect(errorsFor({ expected_guest_count: "100001" }).expected_guest_count).toMatch(/cannot exceed/);
  });

  it("only allows enabled categories and supported currencies", () => {
    expect(errorsFor({ event_type: "birthday" }).event_type).toBeDefined();
    expect(errorsFor({ currency: "JPY" }).currency).toBeDefined();
  });

  it("rejects invalid time zones and country codes", () => {
    expect(errorsFor({ timezone: "Mars/Phobos" }).timezone).toBeDefined();
    expect(errorsFor({ country_code: "IND" }).country_code).toBeDefined();
  });

  it("builds the API body with offsets applied and blanks as null", () => {
    const body = toCreateBody({ ...valid, location_name: " ", city: "Jaipur" });
    expect(body.start_at).toBe("2027-02-12T04:30:00.000Z");
    expect(body.end_at).toBe("2027-02-14T16:30:00.000Z");
    expect(body.location).toEqual({ name: null, city: "Jaipur", region: "Rajasthan", country_code: "IN" });
    expect(body.expected_guest_count).toBe(300);
    expect(body).not.toHaveProperty("owner_user_id");
  });
});
