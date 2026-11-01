import { z } from "zod";

/**
 * Centralised, validated configuration. Nothing else in the app reads process.env.
 *
 * Browser-visible values use the NEXT_PUBLIC_ prefix. API_BASE_URL is server-only:
 * the browser talks to the same-origin BFF and never learns the backend address.
 */
const publicSchema = z.object({
  NEXT_PUBLIC_SUPABASE_URL: z.string().url("NEXT_PUBLIC_SUPABASE_URL must be a URL"),
  NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(20, "NEXT_PUBLIC_SUPABASE_ANON_KEY is required"),
  NEXT_PUBLIC_APP_ENV: z.enum(["development", "test", "production"]).default("development"),
});

const serverSchema = publicSchema.extend({
  API_BASE_URL: z.string().url("API_BASE_URL must be a URL"),
  /** Comma-separated extra origins allowed to call the BFF (the site origin is always allowed). */
  BFF_ALLOWED_ORIGINS: z.string().default(""),
  BACKEND_TIMEOUT_MS: z.coerce.number().int().min(1000).max(60000).default(15000),
});

export type PublicEnv = z.infer<typeof publicSchema>;
export type ServerEnv = z.infer<typeof serverSchema>;

export class ConfigError extends Error {}

function fail(error: z.ZodError): never {
  const detail = error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; ");
  throw new ConfigError(`Invalid environment configuration - ${detail}`);
}

export function parsePublicEnv(source: Record<string, string | undefined>): PublicEnv {
  const r = publicSchema.safeParse(source);
  return r.success ? r.data : fail(r.error);
}

export function parseServerEnv(source: Record<string, string | undefined>): ServerEnv {
  const r = serverSchema.safeParse(source);
  if (!r.success) fail(r.error);
  const env = r.data;
  if (env.NEXT_PUBLIC_APP_ENV === "production") {
    if (!env.NEXT_PUBLIC_SUPABASE_URL.startsWith("https://")) {
      throw new ConfigError("NEXT_PUBLIC_SUPABASE_URL must use https in production");
    }
    if (!env.API_BASE_URL.startsWith("https://")) {
      throw new ConfigError("API_BASE_URL must use https in production");
    }
  }
  return env;
}

let cached: ServerEnv | undefined;

/** Server-side only (Route Handlers, Server Components, middleware). */
export function getServerEnv(): ServerEnv {
  cached ??= parseServerEnv({
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_APP_ENV: process.env.NEXT_PUBLIC_APP_ENV,
    API_BASE_URL: process.env.API_BASE_URL,
    BFF_ALLOWED_ORIGINS: process.env.BFF_ALLOWED_ORIGINS,
    BACKEND_TIMEOUT_MS: process.env.BACKEND_TIMEOUT_MS,
  });
  return cached;
}

export function resetEnvCacheForTests(): void {
  cached = undefined;
}
