import Link from "next/link";

import { Button } from "@/components/ui/button";
import { routes } from "@/config/routes";

export default function NotFound() {
  return (
    <main className="bg-celebration flex min-h-screen flex-col items-center justify-center gap-4 px-4 text-center">
      <p className="text-sm font-medium uppercase tracking-widest text-primary">404</p>
      <h1 className="text-4xl font-semibold">We could not find that page</h1>
      <p className="max-w-md text-muted-foreground">
        The page may have moved, or you may not have access to it.
      </p>
      <Button asChild>
        <Link href={routes.dashboard}>Back to dashboard</Link>
      </Button>
    </main>
  );
}
