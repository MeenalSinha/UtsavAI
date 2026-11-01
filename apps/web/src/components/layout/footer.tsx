import Link from "next/link";
import * as React from "react";

export function Footer() {
  return (
    <footer className="mt-auto border-t bg-card/40 py-6 text-xs text-muted-foreground" aria-label="Footer">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-10">
        <div>
          <p className="font-medium text-foreground">UtsavAI &bull; Production v1.0.0-rc1</p>
          <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
            AI recommendations are advisory and require human review. Vendor estimates are user-provided.
            GiftCircle tracks reservations and does not process payments.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <Link href="/privacy" className="hover:text-foreground underline-offset-4 hover:underline">
            Privacy Policy
          </Link>
          <Link href="/terms" className="hover:text-foreground underline-offset-4 hover:underline">
            Terms of Service
          </Link>
          <Link href="/ai-disclosure" className="hover:text-foreground underline-offset-4 hover:underline">
            AI Disclosure
          </Link>
        </div>
      </div>
    </footer>
  );
}
