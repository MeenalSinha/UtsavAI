import { randomUUID } from "node:crypto";
import type { NextRequest } from "next/server";

import { backendFetch } from "@/lib/api/backend";

export const dynamic = "force-dynamic";

async function handler(
  request: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await ctx.params;
  const pathStr = path.join("/");

  // Allow only public registries paths
  if (!pathStr.startsWith("public/registries/")) {
    return new Response(
      JSON.stringify({
        error: {
          code: "NOT_FOUND",
          message: "The public resource was not found.",
          details: {},
          request_id: `req_${randomUUID().replaceAll("-", "")}`,
        },
      }),
      { status: 404, headers: { "content-type": "application/json" } },
    );
  }

  const requestId = `req_${randomUUID().replaceAll("-", "")}`;
  const method = request.method.toUpperCase();

  let body: string | undefined;
  if (method === "POST" || method === "PATCH" || method === "PUT") {
    body = await request.text();
  }

  const query = request.nextUrl.search;
  const backendPath = `/${pathStr}${query}`;

  const res = await backendFetch({
    method,
    path: backendPath,
    body,
    headers: {
      "content-type": request.headers.get("content-type") || "application/json",
    },
    requestId,
  });

  const responseHeaders = new Headers();
  responseHeaders.set("content-type", res.headers.get("content-type") || "application/json");
  responseHeaders.set("cache-control", "no-store");
  if (res.headers.get("x-request-id")) {
    responseHeaders.set("x-request-id", res.headers.get("x-request-id")!);
  }

  return new Response(res.body, {
    status: res.status,
    headers: responseHeaders,
  });
}

export { handler as GET, handler as POST, handler as PATCH, handler as DELETE };
