export const routes = {
  home: "/",
  signIn: "/sign-in",
  signUp: "/sign-up",
  forgotPassword: "/forgot-password",
  resetPassword: "/reset-password",
  authCallback: "/auth/callback",
  dashboard: "/dashboard",
  events: "/events",
  newEvent: "/events/new",
  event: (id: string) => `/events/${id}`,
  eventPreferences: (id: string) => `/events/${id}/preferences`,
  eventFunctions: (id: string) => `/events/${id}/functions`,
  eventPlanAi: (id: string) => `/events/${id}/plan-ai`,
  eventBudget: (id: string) => `/events/${id}/budget`,
  eventTimeline: (id: string) => `/events/${id}/timeline`,
  profile: "/profile",
} as const;

/** Paths that require a valid server-validated session. */
export const PROTECTED_PREFIXES = ["/dashboard", "/events", "/profile"] as const;
/** Paths a signed-in user is redirected away from. */
export const AUTH_ONLY_PATHS = ["/sign-in", "/sign-up", "/forgot-password"] as const;

export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

export function isAuthOnlyPath(pathname: string): boolean {
  return (AUTH_ONLY_PATHS as readonly string[]).includes(pathname);
}

/** Only same-site relative paths are valid post-login redirects (no open redirects). */
export function safeNextPath(next: string | null | undefined, fallback: string = routes.dashboard): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.includes("\\")) return fallback;
  try {
    const u = new URL(next, "http://placeholder.invalid");
    if (u.origin !== "http://placeholder.invalid") return fallback;
    return `${u.pathname}${u.search}`;
  } catch {
    return fallback;
  }
}
