import "server-only";

import { createServerClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";

import { getServerEnv } from "@/config/env";
import { sessionCookieOptions } from "@/lib/supabase/cookies";

/**
 * Server-side Supabase client bound to the request cookies.
 * Sessions are only ever handled on the server, so cookies are HTTP-only:
 * browser JavaScript can never read the access or refresh token.
 */
export async function createClient(): Promise<SupabaseClient> {
  const env = getServerEnv();
  const cookieStore = await cookies();
  return createServerClient(env.NEXT_PUBLIC_SUPABASE_URL, env.NEXT_PUBLIC_SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => cookieStore.getAll(),
      setAll(toSet) {
        try {
          for (const { name, value, options } of toSet) {
            cookieStore.set(name, value, sessionCookieOptions(options, env.NEXT_PUBLIC_APP_ENV === "production"));
          }
        } catch {
          // Called from a Server Component: cookie writes are handled by middleware instead.
        }
      },
    },
  });
}

/** Validated session -> access token for the BFF. Returns null when not signed in. */
export async function getAccessToken(): Promise<string | null> {
  const supabase = await createClient();
  const { data: userData, error } = await supabase.auth.getUser(); // validates with Supabase Auth
  if (error || !userData.user) return null;
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export async function getCurrentUser() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getUser();
  return error ? null : data.user;
}
