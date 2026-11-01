import "server-only";

import { getServerEnv } from "@/config/env";

export interface BackendRequest {
  method: string;
  path: string; // e.g. /events?limit=10 (relative to /api/v1)
  accessToken?: string;
  body?: string;
  headers?: Record<string, string>;
  requestId?: string;
  fetchImpl?: typeof fetch;
  baseUrl?: string;
  timeoutMs?: number;
}

/** Single place that calls FastAPI. Used by the BFF and by Server Components. */
export async function backendFetch(req: BackendRequest): Promise<Response> {
  const env = getServerEnv();
  const base = (req.baseUrl ?? env.API_BASE_URL).replace(/\/$/, "");
  const headers = new Headers(req.headers);
  headers.set("Accept", "application/json");
  if (req.accessToken) headers.set("Authorization", `Bearer ${req.accessToken}`);
  if (req.requestId) headers.set("X-Request-ID", req.requestId);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), req.timeoutMs ?? env.BACKEND_TIMEOUT_MS);
  try {
    return await (req.fetchImpl ?? fetch)(`${base}/api/v1${req.path}`, {
      method: req.method,
      headers,
      body: req.body,
      signal: controller.signal,
      cache: "no-store",
      redirect: "manual",
    });
  } finally {
    clearTimeout(timer);
  }
}
