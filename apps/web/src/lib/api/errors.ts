import type { ApiErrorBody } from "@/types/api";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details: Record<string, unknown> = {},
    public readonly requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }

  /** Field-level messages from VALIDATION_ERROR responses, keyed by field path. */
  get fieldErrors(): Record<string, string> {
    const fields = this.details.fields;
    if (!Array.isArray(fields)) return {};
    const out: Record<string, string> = {};
    for (const f of fields) {
      if (f && typeof f === "object" && "field" in f && "message" in f) {
        out[String(f.field)] ??= String(f.message);
      }
    }
    return out;
  }

  get isConflict(): boolean {
    return this.status === 409;
  }
  get isUnauthenticated(): boolean {
    return this.status === 401;
  }
}

export function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as ApiErrorBody).error?.code === "string"
  );
}

export async function toApiError(response: Response): Promise<ApiError> {
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    /* non-JSON error body */
  }
  if (isApiErrorBody(body)) {
    const e = body.error;
    return new ApiError(response.status, e.code, e.message, e.details ?? {}, e.request_id ?? null);
  }
  return new ApiError(response.status, "UNKNOWN_ERROR", "Something went wrong. Please try again.");
}

export function userMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 503 || error.status === 502) return "The service is temporarily unavailable. Please try again shortly.";
    if (error.status >= 500) return "Something went wrong on our side. Please try again.";
    return error.message;
  }
  return "Something went wrong. Please try again.";
}
