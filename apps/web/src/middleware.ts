import type { NextRequest } from "next/server";

import { updateSession } from "@/lib/supabase/middleware";

export async function middleware(request: NextRequest) {
  return updateSession(request);
}

export const config = {
  matcher: [
    // Skip static assets and the BFF (it validates the session itself and must return JSON 401s).
    "/((?!_next/static|_next/image|favicon.ico|api/bff|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
