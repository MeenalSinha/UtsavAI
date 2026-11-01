/** Date and time-zone helpers. All conversion uses Intl; no date library is needed. */

const partsCache = new Map<string, Intl.DateTimeFormat>();

function formatter(tz: string): Intl.DateTimeFormat {
  let f = partsCache.get(tz);
  if (!f) {
    f = new Intl.DateTimeFormat("en-CA", {
      timeZone: tz,
      hourCycle: "h23",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    partsCache.set(tz, f);
  }
  return f;
}

function partsOf(ms: number, tz: string): Record<string, number> {
  const out: Record<string, number> = {};
  for (const p of formatter(tz).formatToParts(new Date(ms))) {
    if (p.type !== "literal") out[p.type] = Number(p.value);
  }
  return out;
}

/** Offset of `tz` from UTC at the given instant, in milliseconds. */
function offsetMs(ms: number, tz: string): number {
  const p = partsOf(ms, tz);
  const asUtc = Date.UTC(p.year!, p.month! - 1, p.day!, p.hour!, p.minute!, p.second!);
  return asUtc - Math.floor(ms / 1000) * 1000;
}

export function isValidTimeZone(tz: string): boolean {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: tz });
    return tz.includes("/") || tz === "UTC";
  } catch {
    return false;
  }
}

const LOCAL_RE = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/;

/** "2027-02-12T10:00" interpreted as wall-clock time in `tz` -> UTC ISO string (…Z). */
export function zonedLocalToUtcIso(local: string, tz: string): string | null {
  const m = LOCAL_RE.exec(local);
  if (!m || !isValidTimeZone(tz)) return null;
  const [, y, mo, d, h, mi] = m.map(Number) as [number, number, number, number, number, number];
  const naive = Date.UTC(y, mo - 1, d, h, mi, 0);
  if (new Date(naive).getUTCMonth() !== mo - 1) return null; // e.g. 31 February
  // Two-pass fixed point handles DST boundaries.
  let guess = naive - offsetMs(naive, tz);
  guess = naive - offsetMs(guess, tz);
  return new Date(guess).toISOString();
}

/** UTC ISO instant -> "YYYY-MM-DDTHH:mm" wall-clock in `tz` (for datetime-local inputs). */
export function utcIsoToZonedLocal(iso: string, tz: string): string {
  const p = partsOf(Date.parse(iso), tz);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${p.year}-${pad(p.month!)}-${pad(p.day!)}T${pad(p.hour!)}:${pad(p.minute!)}`;
}

export function formatEventRange(startIso: string, endIso: string, tz: string, locale = "en-IN"): string {
  const day = new Intl.DateTimeFormat(locale, { timeZone: tz, day: "numeric", month: "short", year: "numeric" });
  const time = new Intl.DateTimeFormat(locale, { timeZone: tz, hour: "numeric", minute: "2-digit" });
  const start = new Date(startIso);
  const end = new Date(endIso);
  const sameDay = day.format(start) === day.format(end);
  return sameDay
    ? `${day.format(start)}, ${time.format(start)} - ${time.format(end)}`
    : `${day.format(start)} - ${day.format(end)}`;
}

export function formatDateTime(iso: string, tz: string, locale = "en-IN"): string {
  return new Intl.DateTimeFormat(locale, {
    timeZone: tz,
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short",
  }).format(new Date(iso));
}

export function supportedTimeZones(extra: string[] = []): string[] {
  let zones: string[] = [];
  try {
    zones = (Intl as unknown as { supportedValuesOf?: (k: string) => string[] }).supportedValuesOf?.("timeZone") ?? [];
  } catch {
    zones = [];
  }
  return Array.from(new Set([...extra, ...zones])).sort();
}

export function browserTimeZone(): string | null {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null;
  } catch {
    return null;
  }
}
