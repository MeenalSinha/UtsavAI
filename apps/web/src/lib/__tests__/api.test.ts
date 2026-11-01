import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api/client";
import { ApiError, toApiError, userMessage } from "@/lib/api/errors";
import { sessionCookieOptions } from "@/lib/supabase/cookies";

afterEach(() => vi.unstubAllGlobals());

const envelope = (code: string, message: string, details = {}) => ({ error: { code, message, details, request_id: "req_1" } });

describe("API errors", () => {
  it("parses the documented error envelope", async () => {
    const res = new Response(JSON.stringify(envelope("VALIDATION_ERROR", "The event date range is invalid.", { fields: [{ field: "end_at", message: "bad" }] })), { status: 422 });
    const err = await toApiError(res);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("VALIDATION_ERROR");
    expect(err.requestId).toBe("req_1");
    expect(err.fieldErrors).toEqual({ end_at: "bad" });
  });

  it("falls back for non-JSON failures and hides server details", async () => {
    const err = await toApiError(new Response("<html>boom</html>", { status: 500 }));
    expect(err.code).toBe("UNKNOWN_ERROR");
    expect(userMessage(err)).toMatch(/our side/);
    expect(userMessage(new ApiError(503, "DEPENDENCY_UNAVAILABLE", "x"))).toMatch(/temporarily unavailable/);
    expect(userMessage(new ApiError(422, "VALIDATION_ERROR", "The event date range is invalid."))).toBe("The event date range is invalid.");
  });
});

describe("apiFetch (browser to BFF)", () => {
  it("calls the same-origin BFF with JSON, If-Match and no credentials in the URL", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ id: "1" }), { status: 200, headers: { etag: '"5"' } }));
    vi.stubGlobal("fetch", fetchMock);
    const out = await apiFetch<{ id: string }>("/events/1", { method: "PATCH", json: { title: "x" }, ifMatch: 4 });
    expect(out).toEqual({ data: { id: "1" }, etag: '"5"' });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/bff/events/1");
    const headers = init.headers as Headers;
    expect(headers.get("If-Match")).toBe('"4"');
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(init.credentials).toBe("same-origin");
    expect(init.body).toBe('{"title":"x"}');
  });

  it("throws ApiError with the server message on failures", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(envelope("REVISION_CONFLICT", "changed")), { status: 409 })));
    await expect(apiFetch("/events/1", { method: "PATCH", json: {} })).rejects.toMatchObject({ status: 409, code: "REVISION_CONFLICT", isConflict: true });
  });

  it("reports network failures clearly", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    await expect(apiFetch("/me")).rejects.toMatchObject({ code: "NETWORK_ERROR" });
  });

  it("sends the user to sign-in when the session has expired", async () => {
    const assign = vi.fn();
    vi.stubGlobal("location", { pathname: "/events/abc", assign });
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(envelope("UNAUTHENTICATED", "expired")), { status: 401 })));
    await expect(apiFetch("/me")).rejects.toMatchObject({ status: 401 });
    expect(assign).toHaveBeenCalledWith("/sign-in?reason=expired&next=%2Fevents%2Fabc");
  });

  it("returns undefined data for 204", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(null, { status: 204 })));
    expect((await apiFetch("/events/1", { method: "DELETE" })).data).toBeUndefined();
  });
});

describe("session cookies", () => {
  it("are always HTTP-only, SameSite=Lax and Secure in production", () => {
    const o = sessionCookieOptions({ httpOnly: false, sameSite: "none", maxAge: 100 }, true);
    expect(o).toMatchObject({ httpOnly: true, sameSite: "lax", secure: true, path: "/", maxAge: 100 });
    expect(sessionCookieOptions(undefined, false).secure).toBe(false);
  });
});
