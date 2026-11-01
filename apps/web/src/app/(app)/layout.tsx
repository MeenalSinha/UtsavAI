import { redirect } from "next/navigation";
import * as React from "react";

import { AppShell } from "@/components/layout/app-shell";
import { routes } from "@/config/routes";
import { getCurrentUser } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

/** Defence in depth: middleware already redirects, this re-validates on the server. */
export default async function AuthenticatedLayout({ children }: { children: React.ReactNode }) {
  const user = await getCurrentUser();
  if (!user) redirect(routes.signIn);
  const meta = (user.user_metadata ?? {}) as Record<string, unknown>;
  const name = typeof meta.display_name === "string" && meta.display_name ? meta.display_name : (user.email?.split("@")[0] ?? "Guest");
  return (
    <AppShell displayName={name} email={user.email ?? null}>
      {children}
    </AppShell>
  );
}
