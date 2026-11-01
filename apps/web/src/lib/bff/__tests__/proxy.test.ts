import { describe, expect, it, vi } from "vitest";

import { handleBffRequest, type BffDeps } from "@/lib/bff/proxy";

const ORIGIN = "https://app.example.com";
const EVENT_ID = "b8d2f1b4-28e4-4b77-a9a4-5f26dc8cbade";

function deps(overrides: Partial<BffDeps> = {}) {
  const forward = vi.fn(async () =>
    new Response(JSON.stringify({ ok: true }), { status: 200, headers: { "content-type": "application/json", etag: '"2"' } }),
  );
  const d: BffDeps = {
    getAccessToken: async () => "jwt-token",
    forward,
    allowedOrigins: [ORIGIN],
    newRequestId: () => "req_test",
    ...overrides,
  };
  return { d, forward };
}

function req(method: string, path: string, init: { headers?: Record<string, string>; body?: string } = {}) {
  return new Request(`${ORIGIN}/api/bff/${path}`, { method, headers: init.headers, body: init.body });
}

const json = { "content-type": "application/json", origin: ORIGIN };

describe("BFF proxy", () => {
  it("forwards the validated access token as a bearer credential and preserves ETag", async () => {
    const { d, forward } = deps();
    const res = await handleBffRequest(req("GET", "events"), ["events"], d);
    expect(res.status).toBe(200);
    expect(res.headers.get("etag")).toBe('"2"');
    expect(forward).toHaveBeenCalledWith(expect.objectContaining({ method: "GET", path: "/events", accessToken: "jwt-token", requestId: "req_test" }));
  });

  it("returns a 401 envelope without calling the backend when there is no session", async () => {
    const { d, forward } = deps({ getAccessToken: async () => null });
    const res = await handleBffRequest(req("GET", "events"), ["events"], d);
    expect(res.status).toBe(401);
    expect((await res.json()).error.code).toBe("UNAUTHENTICATED");
    expect(forward).not.toHaveBeenCalled();
  });

  it("rejects cross-origin mutations (CSRF) before touching the session or backend", async () => {
    const getAccessToken = vi.fn(async () => "jwt-token");
    const { d, forward } = deps({ getAccessToken });
    const res = await handleBffRequest(
      req("POST", "events", { headers: { ...json, origin: "https://evil.example" }, body: "{}" }),
      ["events"],
      d,
    );
    expect(res.status).toBe(403);
    expect(getAccessToken).not.toHaveBeenCalled();
    expect(forward).not.toHaveBeenCalled();
  });

  it("accepts a mutation without Origin only when the browser reports same-origin", async () => {
    const { d } = deps();
    const ok = await handleBffRequest(
      req("DELETE", `events/${EVENT_ID}`, { headers: { "sec-fetch-site": "same-origin" } }),
      ["events", EVENT_ID],
      d,
    );
    expect(ok.status).toBe(200);
    const bad = await handleBffRequest(
      req("DELETE", `events/${EVENT_ID}`, { headers: { "sec-fetch-site": "cross-site" } }),
      ["events", EVENT_ID],
      d,
    );
    expect(bad.status).toBe(403);
    const none = await handleBffRequest(req("DELETE", `events/${EVENT_ID}`), ["events", EVENT_ID], d);
    expect(none.status).toBe(403);
  });

  it("only exposes allow-listed routes and methods", async () => {
    const { d, forward } = deps();
    expect((await handleBffRequest(req("GET", "health/ready"), ["health", "ready"], d)).status).toBe(404);
    expect((await handleBffRequest(req("GET", "events/not-a-uuid"), ["events", "not-a-uuid"], d)).status).toBe(404);
    expect((await handleBffRequest(req("GET", "events/../me"), ["events", "..", "me"], d)).status).toBe(404);
    expect((await handleBffRequest(req("DELETE", "events", { headers: json }), ["events"], d)).status).toBe(405);
    expect((await handleBffRequest(req("PUT", "me", { headers: json }), ["me"], d)).status).toBe(405);
    expect(forward).not.toHaveBeenCalled();
  });

  it("forwards If-Match and JSON body on updates", async () => {
    const { d, forward } = deps();
    await handleBffRequest(
      req("PATCH", `events/${EVENT_ID}`, { headers: { ...json, "if-match": '"4"' }, body: '{"title":"x"}' }),
      ["events", EVENT_ID],
      d,
    );
    expect(forward).toHaveBeenCalledWith(
      expect.objectContaining({ method: "PATCH", body: '{"title":"x"}', headers: { "Content-Type": "application/json", "If-Match": '"4"' } }),
    );
  });

  it("requires JSON bodies and bounds their size", async () => {
    const { d } = deps();
    const wrong = await handleBffRequest(req("POST", "events", { headers: { "content-type": "text/plain", origin: ORIGIN }, body: "x" }), ["events"], d);
    expect(wrong.status).toBe(400);
    const big = await handleBffRequest(req("POST", "events", { headers: json, body: "x".repeat(70_000) }), ["events"], d);
    expect(big.status).toBe(413);
  });

  it("forwards only allow-listed query parameters", async () => {
    const { d, forward } = deps();
    const r = new Request(`${ORIGIN}/api/bff/events?limit=5&status=archived&evil=1&owner_user_id=x`);
    await handleBffRequest(r, ["events"], d);
    expect(forward).toHaveBeenCalledWith(expect.objectContaining({ path: "/events?limit=5&status=archived" }));
  });

  it("passes backend error envelopes through and never forwards the token to the browser", async () => {
    const err = { error: { code: "REVISION_CONFLICT", message: "changed", details: {}, request_id: "req_b" } };
    const { d } = deps({ forward: async () => new Response(JSON.stringify(err), { status: 409, headers: { "content-type": "application/json" } }) });
    const res = await handleBffRequest(req("GET", `events/${EVENT_ID}`), ["events", EVENT_ID], d);
    expect(res.status).toBe(409);
    expect((await res.json()).error.code).toBe("REVISION_CONFLICT");
    expect(JSON.stringify([...res.headers.entries()])).not.toContain("jwt-token");
  });

  it("maps backend outages to 503 without leaking details and handles 204", async () => {
    const down = deps({ forward: async () => { throw new Error("ECONNREFUSED 10.0.0.5:8000"); } });
    const res = await handleBffRequest(req("GET", "me"), ["me"], down.d);
    expect(res.status).toBe(503);
    expect(await res.text()).not.toContain("10.0.0.5");
    const empty = deps({ forward: async () => new Response(null, { status: 204 }) });
    const noContent = await handleBffRequest(req("DELETE", `events/${EVENT_ID}`, { headers: { origin: ORIGIN } }), ["events", EVENT_ID], empty.d);
    expect(noContent.status).toBe(204);
  });
});
