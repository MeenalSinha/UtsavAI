import "server-only";

import { backendFetch } from "@/lib/api/backend";
import { ApiError, toApiError } from "@/lib/api/errors";
import { getAccessToken } from "@/lib/supabase/server";

/** Server Components call FastAPI directly with the validated session's access token. */
export async function serverGet<T>(path: string): Promise<T> {
  const accessToken = await getAccessToken();
  if (!accessToken) throw new ApiError(401, "UNAUTHENTICATED", "Your session has expired. Please sign in again.");
  let response: Response;
  try {
    response = await backendFetch({ method: "GET", path, accessToken });
  } catch {
    throw new ApiError(503, "DEPENDENCY_UNAVAILABLE", "The service is temporarily unavailable.");
  }
  if (!response.ok) throw await toApiError(response);
  return (await response.json()) as T;
}

/** Public, non-secret configuration published by the backend (categories, currencies, limits). */
export async function fetchMeta<T>(): Promise<T> {
  let response: Response;
  try {
    response = await backendFetch({ method: "GET", path: "/meta" });
  } catch {
    throw new ApiError(503, "DEPENDENCY_UNAVAILABLE", "The service is temporarily unavailable.");
  }
  if (!response.ok) throw await toApiError(response);
  return (await response.json()) as T;
}
