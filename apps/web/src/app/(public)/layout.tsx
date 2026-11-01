import Link from "next/link";
import * as React from "react";

import { Footer } from "@/components/layout/footer";
import { Logo } from "@/components/layout/logo";
import { buttonVariants } from "@/components/ui/button";
import { routes } from "@/config/routes";

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="sticky top-0 z-30 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-10">
          <Link href={routes.home} aria-label="UtsavAI Home">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            <Link href={routes.signIn} className={buttonVariants({ variant: "outline", size: "sm" })}>
              Sign in
            </Link>
            <Link href={routes.signUp} className={buttonVariants({ size: "sm" })}>
              Get started
            </Link>
          </div>
        </div>
      </header>
      <main className="flex-1 px-4 py-12 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-4xl">{children}</div>
      </main>
      <Footer />
    </div>
  );
}
