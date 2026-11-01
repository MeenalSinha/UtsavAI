import { randomUUID } from "node:crypto";
import type { NextRequest } from "next/server";

import { getServerEnv } from "@/config/env";
import { backendFetch } from "@/lib/api/backend";
import { handleBffRequest } from "@/lib/bff/proxy";
import { getAccessToken } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

async function handler(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }): Promise<Response> {
  const { path } = await ctx.params;
  const env = getServerEnv();
  const extra = env.BFF_ALLOWED_ORIGINS.split(",").map((o) => o.trim()).filter(Boolean);
  return handleBffRequest(request, path, {
    getAccessToken,
    forward: (r) =>
      backendFetch({
        method: r.method,
        path: r.path,
        accessToken: r.accessToken,
        body: r.body,
        headers: r.headers,
        requestId: r.requestId,
      }),
    allowedOrigins: [request.nextUrl.origin, ...extra],
    newRequestId: () => `req_${randomUUID().replaceAll("-", "")}`,
  });
}

export { handler as GET, handler as POST, handler as PATCH, handler as DELETE };
