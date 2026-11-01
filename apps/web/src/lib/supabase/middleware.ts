import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { getServerEnv } from "@/config/env";
import { isAuthOnlyPath, isProtectedPath, routes } from "@/config/routes";
import { sessionCookieOptions } from "@/lib/supabase/cookies";

export type GuardDecision = { action: "next" } | { action: "redirect"; to: string };

/** Pure routing decision, unit-tested separately from Next.js plumbing. */
export function decideAccess(pathname: string, search: string, signedIn: boolean): GuardDecision {
  if (!signedIn && isProtectedPath(pathname)) {
    const next = encodeURIComponent(`${pathname}${search}`);
    return { action: "redirect", to: `${routes.signIn}?next=${next}` };
  }
  if (signedIn && isAuthOnlyPath(pathname)) return { action: "redirect", to: routes.dashboard };
  return { action: "next" };
}

/**
 * Refreshes the session on every matched request (rotating cookies when needed) and
 * enforces route protection. Validation uses getUser(), which asks Supabase Auth
 * rather than trusting cookie contents.
 */
export async function updateSession(request: NextRequest): Promise<NextResponse> {
  const env = getServerEnv();
  let response = NextResponse.next({ request });

  const supabase = createServerClient(env.NEXT_PUBLIC_SUPABASE_URL, env.NEXT_PUBLIC_SUPABASE_ANON_KEY, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll(toSet) {
        for (const { name, value } of toSet) request.cookies.set(name, value);
        response = NextResponse.next({ request });
        for (const { name, value, options } of toSet) {
          response.cookies.set(name, value, sessionCookieOptions(options, env.NEXT_PUBLIC_APP_ENV === "production"));
        }
      },
    },
  });

  const { data } = await supabase.auth.getUser();
  const decision = decideAccess(request.nextUrl.pathname, request.nextUrl.search, Boolean(data.user));

  if (decision.action === "redirect") {
    const redirect = NextResponse.redirect(new URL(decision.to, request.url));
    // Carry refreshed/cleared cookies onto the redirect.
    for (const c of response.cookies.getAll()) redirect.cookies.set(c);
    return redirect;
  }
  return response;
}
