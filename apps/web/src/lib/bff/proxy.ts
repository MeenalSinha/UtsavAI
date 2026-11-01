/**
 * Pure BFF request handler (dependency-injected for testing).
 *
 * Responsibilities, and nothing more: validate the session, enforce origin
 * (CSRF) checks on mutations, allow-list routes, forward the access token to
 * FastAPI, and map transport failures. No business rules live here.
 */
export interface BffDeps {
  getAccessToken: () => Promise<string | null>;
  forward: (req: {
    method: string;
    path: string;
    accessToken: string;
    body?: string;
    headers: Record<string, string>;
    requestId: string;
  }) => Promise<Response>;
  allowedOrigins: string[];
  newRequestId: () => string;
}

const UUID = "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";
const ROUTES: { pattern: RegExp; methods: ReadonlySet<string> }[] = [
  { pattern: /^me$/, methods: new Set(["GET", "PATCH"]) },
  { pattern: /^events$/, methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}$`), methods: new Set(["GET", "PATCH", "DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/context$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/preferences$`), methods: new Set(["GET", "PUT"]) },
  { pattern: new RegExp(`^events/${UUID}/functions$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/functions/${UUID}$`), methods: new Set(["PATCH", "DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/ai/conversations$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/ai/conversations/${UUID}$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/ai/conversations/${UUID}/messages$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/plans/generate$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/ai/proposals/${UUID}$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/ai/proposals/${UUID}/accept$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/ai/proposals/${UUID}/reject$`), methods: new Set(["POST"]) },
  // Phase 3: BudgetAI & TimelineAI
  { pattern: new RegExp(`^events/${UUID}/budget$`), methods: new Set(["GET", "POST", "PATCH"]) },
  { pattern: new RegExp(`^events/${UUID}/budget/categories$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/budget/categories/${UUID}$`), methods: new Set(["PATCH", "DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/budget/summary$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/budget/ai/generate$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/budget/ai/proposals/${UUID}/accept$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/expenses$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/expenses/${UUID}$`), methods: new Set(["PATCH", "DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/tasks$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/tasks/${UUID}$`), methods: new Set(["GET", "PATCH", "DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/tasks/${UUID}/dependencies$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/tasks/${UUID}/dependencies/${UUID}$`), methods: new Set(["DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/tasks/summary$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/timeline/summary$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/timeline/ai/generate$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/timeline/ai/proposals/${UUID}/accept$`), methods: new Set(["POST"]) },
  // Phase 4: VendorConnect
  { pattern: new RegExp(`^events/${UUID}/vendors$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/vendors/summary$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/vendors/${UUID}$`), methods: new Set(["GET", "PATCH", "DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/vendors/${UUID}/quotes$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/vendors/${UUID}/quotes/${UUID}$`), methods: new Set(["PATCH"]) },
  { pattern: new RegExp(`^events/${UUID}/vendor-quote-comparison$`), methods: new Set(["GET"]) },
  // Phase 5: GiftCircle (Host)
  { pattern: new RegExp(`^events/${UUID}/gift-registry$`), methods: new Set(["GET", "POST", "PATCH"]) },
  { pattern: new RegExp(`^events/${UUID}/gift-registry/share-link$`), methods: new Set(["GET", "POST", "DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/gift-registry/overview$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/gift-registry/items$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/gift-registry/items/${UUID}$`), methods: new Set(["PATCH", "DELETE"]) },
  { pattern: new RegExp(`^events/${UUID}/gift-registry/reservations$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/gift-registry/reservations/${UUID}/cancel$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/gift-registry/contributions$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/gift-registry/contributions/${UUID}/verify$`), methods: new Set(["POST"]) },
  // Phase 6: Adaptive Planning Engine
  { pattern: new RegExp(`^events/${UUID}/change-proposals$`), methods: new Set(["GET", "POST"]) },
  { pattern: new RegExp(`^events/${UUID}/change-proposals/interpret$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/change-proposals/${UUID}$`), methods: new Set(["GET"]) },
  { pattern: new RegExp(`^events/${UUID}/change-proposals/${UUID}/accept$`), methods: new Set(["POST"]) },
  { pattern: new RegExp(`^events/${UUID}/change-proposals/${UUID}/reject$`), methods: new Set(["POST"]) },
];
const FORWARDED_QUERY_KEYS = new Set([
  "limit",
  "offset",
  "cursor",
  "status",
  "include_archived",
  "sort",
  "category",
  "search",
  "priority",
  "item_type",
  "gift_mode",
]);
const MUTATING = new Set(["POST", "PATCH", "PUT", "DELETE"]);
const MAX_BODY_BYTES = 64 * 1024;

function envelope(status: number, code: string, message: string, requestId: string): Response {
  return new Response(JSON.stringify({ error: { code, message, details: {}, request_id: requestId } }), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store", "x-request-id": requestId },
  });
}

export function originAllowed(request: Request, allowed: string[]): boolean {
  const origin = request.headers.get("origin");
  if (origin) return allowed.includes(origin);
  // Some same-origin requests omit Origin; accept only when the browser says same-origin.
  return request.headers.get("sec-fetch-site") === "same-origin";
}

export async function handleBffRequest(request: Request, segments: string[], deps: BffDeps): Promise<Response> {
  const requestId = deps.newRequestId();
  const method = request.method.toUpperCase();
  const path = segments.join("/");

  const route = ROUTES.find((r) => r.pattern.test(path));
  if (!route) return envelope(404, "NOT_FOUND", "The resource was not found.", requestId);
  if (!route.methods.has(method)) {
    return envelope(405, "INVALID_REQUEST", "The method is not allowed for this resource.", requestId);
  }

  if (MUTATING.has(method) && !originAllowed(request, deps.allowedOrigins)) {
    return envelope(403, "FORBIDDEN", "The request origin is not allowed.", requestId);
  }

  const accessToken = await deps.getAccessToken();
  if (!accessToken) return envelope(401, "UNAUTHENTICATED", "Your session has expired. Please sign in again.", requestId);

  let body: string | undefined;
  const headers: Record<string, string> = {};
  if (method === "POST" || method === "PATCH") {
    const contentType = request.headers.get("content-type") ?? "";
    if (!contentType.toLowerCase().startsWith("application/json")) {
      return envelope(400, "INVALID_REQUEST", "The request must be JSON.", requestId);
    }
    body = await request.text();
    if (new TextEncoder().encode(body).length > MAX_BODY_BYTES) {
      return envelope(413, "PAYLOAD_TOO_LARGE", "The request body is too large.", requestId);
    }
    headers["Content-Type"] = "application/json";
  }
  const ifMatch = request.headers.get("if-match");
  if (ifMatch) headers["If-Match"] = ifMatch;

  const url = new URL(request.url);
  const query = new URLSearchParams();
  url.searchParams.forEach((value, key) => {
    if (FORWARDED_QUERY_KEYS.has(key)) query.append(key, value);
  });
  const qs = query.toString();

  let upstream: Response;
  try {
    upstream = await deps.forward({
      method,
      path: `/${path}${qs ? `?${qs}` : ""}`,
      accessToken,
      body,
      headers,
      requestId,
    });
  } catch {
    return envelope(503, "DEPENDENCY_UNAVAILABLE", "The service is temporarily unavailable.", requestId);
  }

  const out = new Headers({ "cache-control": "no-store", "x-request-id": upstream.headers.get("x-request-id") ?? requestId });
  for (const name of ["content-type", "etag", "location"]) {
    const v = upstream.headers.get(name);
    if (v) out.set(name, v);
  }
  if (upstream.status === 204) return new Response(null, { status: 204, headers: out });
  return new Response(await upstream.text(), { status: upstream.status, headers: out });
}
