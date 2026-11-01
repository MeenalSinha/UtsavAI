import { LogOut } from "lucide-react";
import Link from "next/link";
import * as React from "react";

import { Logo } from "@/components/layout/logo";
import { NavLinks } from "@/components/layout/nav-links";
import { Button } from "@/components/ui/button";
import { routes } from "@/config/routes";
import { signOutAction } from "@/features/auth/actions";

export function AppShell({ displayName, email, children }: { displayName: string; email: string | null; children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background lg:grid lg:grid-cols-[16rem_1fr]">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-card focus:px-4 focus:py-2">
        Skip to content
      </a>
      <aside className="hidden border-r bg-card/70 lg:flex lg:flex-col lg:p-5" aria-label="Sidebar">
        <Link href={routes.dashboard} aria-label="UtsavAI dashboard">
          <Logo />
        </Link>
        <nav aria-label="Main" className="mt-8 flex-1">
          <NavLinks orientation="vertical" />
        </nav>
        <p className="text-xs text-muted-foreground">Private and secure. Only you can see your events.</p>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
          <div className="flex h-16 items-center justify-between gap-4 px-4 sm:px-6">
            <Link href={routes.dashboard} className="lg:hidden" aria-label="UtsavAI dashboard">
              <Logo compact />
            </Link>
            <div className="hidden min-w-0 lg:block" />
            <div className="flex items-center gap-3">
              <div className="hidden text-right sm:block">
                <p className="text-sm font-medium leading-tight">{displayName}</p>
                {email && <p className="text-xs text-muted-foreground">{email}</p>}
              </div>
              <form action={signOutAction}>
                <Button type="submit" variant="outline" size="sm">
                  <LogOut className="h-4 w-4" aria-hidden /> Sign out
                </Button>
              </form>
            </div>
          </div>
          <nav aria-label="Main (mobile)" className="overflow-x-auto border-t px-3 py-2 lg:hidden">
            <NavLinks orientation="horizontal" />
          </nav>
        </header>
        <main id="main" className="flex-1 px-4 py-8 sm:px-6 lg:px-10">
          <div className="mx-auto w-full max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
