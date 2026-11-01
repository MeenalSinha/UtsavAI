import { describe, expect, it } from "vitest";

import { formatEventRange, isValidTimeZone, utcIsoToZonedLocal, zonedLocalToUtcIso } from "@/features/events/datetime";

describe("time zone conversion", () => {
  it("converts wall-clock time in Asia/Kolkata (UTC+5:30) to UTC", () => {
    expect(zonedLocalToUtcIso("2027-02-12T10:00", "Asia/Kolkata")).toBe("2027-02-12T04:30:00.000Z");
  });

  it("round-trips through a zone", () => {
    const iso = zonedLocalToUtcIso("2027-02-12T22:15", "Asia/Kolkata")!;
    expect(utcIsoToZonedLocal(iso, "Asia/Kolkata")).toBe("2027-02-12T22:15");
  });

  it("respects daylight saving time", () => {
    expect(zonedLocalToUtcIso("2027-01-15T12:00", "America/New_York")).toBe("2027-01-15T17:00:00.000Z");
    expect(zonedLocalToUtcIso("2027-07-15T12:00", "America/New_York")).toBe("2027-07-15T16:00:00.000Z");
  });

  it("rejects impossible dates and unknown zones", () => {
    expect(zonedLocalToUtcIso("2027-02-31T10:00", "Asia/Kolkata")).toBeNull();
    expect(zonedLocalToUtcIso("not-a-date", "Asia/Kolkata")).toBeNull();
    expect(zonedLocalToUtcIso("2027-02-12T10:00", "Mars/Phobos")).toBeNull();
  });

  it("validates IANA zone names", () => {
    expect(isValidTimeZone("Asia/Kolkata")).toBe(true);
    expect(isValidTimeZone("UTC")).toBe(true);
    expect(isValidTimeZone("Mars/Phobos")).toBe(false);
    expect(isValidTimeZone("")).toBe(false);
  });

  it("formats single-day and multi-day ranges in the event time zone", () => {
    expect(formatEventRange("2027-02-12T04:30:00Z", "2027-02-14T16:30:00Z", "Asia/Kolkata")).toContain("12 Feb 2027");
    const single = formatEventRange("2027-02-12T04:30:00Z", "2027-02-12T16:30:00Z", "Asia/Kolkata");
    expect(single).toMatch(/10:00/);
  });
});
