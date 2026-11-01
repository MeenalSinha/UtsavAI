import type { CookieOptions } from "@supabase/ssr";

/** Forces HTTP-only, SameSite=Lax, Secure (in production) on every session cookie. */
export function sessionCookieOptions(options: CookieOptions | undefined, secure: boolean): CookieOptions {
  return { ...options, httpOnly: true, sameSite: "lax", secure, path: "/" };
}
