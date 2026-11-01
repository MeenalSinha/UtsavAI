import "server-only";

import { notFound, redirect } from "next/navigation";

import { routes } from "@/config/routes";
import { ApiError } from "@/lib/api/errors";

/** Maps API failures onto Next.js navigation: 401 -> sign-in, 404 -> not-found, else error boundary. */
export async function loadOrNavigate<T>(promise: Promise<T>, nextPath?: string): Promise<T> {
  try {
    return await promise;
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 401) {
        const next = nextPath ? `&next=${encodeURIComponent(nextPath)}` : "";
        redirect(`${routes.signIn}?reason=expired${next}`);
      }
      if (error.status === 404) notFound();
    }
    throw error;
  }
}
