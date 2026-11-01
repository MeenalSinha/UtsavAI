"use client";

import { routes } from "@/config/routes";
import { ApiError, toApiError } from "@/lib/api/errors";

const BFF_PREFIX = "/api/bff";

export interface ApiResult<T> {
  data: T;
  etag: string | null;
}

/** Browser -> same-origin BFF. Never talks to FastAPI or Supabase directly. */
export async function apiFetch<T>(
  path: string,
  init: Omit<RequestInit, "body"> & { json?: unknown; ifMatch?: number } = {},
): Promise<ApiResult<T>> {
  const { json, ifMatch, headers, ...rest } = init;
  const finalHeaders = new Headers(headers);
  finalHeaders.set("Accept", "application/json");
  if (json !== undefined) finalHeaders.set("Content-Type", "application/json");
  if (ifMatch !== undefined) finalHeaders.set("If-Match", `"${ifMatch}"`);

  let response: Response;
  try {
    response = await fetch(`${BFF_PREFIX}${path}`, {
      ...rest,
      headers: finalHeaders,
      body: json === undefined ? undefined : JSON.stringify(json),
      credentials: "same-origin",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Could not reach the server. Check your connection and try again.");
  }

  if (response.status === 401 && typeof window !== "undefined") {
    const next = encodeURIComponent(window.location.pathname);
    window.location.assign(`${routes.signIn}?reason=expired&next=${next}`);
  }
  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return { data: undefined as T, etag: null };
  return { data: (await response.json()) as T, etag: response.headers.get("etag") };
}
