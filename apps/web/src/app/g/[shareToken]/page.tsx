import type { Metadata } from "next";
import Link from "next/link";
import { Gift } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PublicRegistryView } from "@/features/gifts/components/public-registry-view";
import type { PublicGiftRegistryDto } from "@/features/gifts/types";
import { backendFetch } from "@/lib/api/backend";

export const metadata: Metadata = {
  title: "Wedding Gift Registry | UtsavAI",
  description: "Browse the couple's wedding registry, reserve items, and contribute to group gifts.",
};

export default async function PublicRegistryPage({
  params,
}: {
  params: Promise<{ shareToken: string }>;
}) {
  const { shareToken } = await params;

  let registry: PublicGiftRegistryDto | null = null;
  try {
    const res = await backendFetch({
      method: "GET",
      path: `/public/registries/${shareToken}`,
    });
    if (res.ok) {
      registry = (await res.json()) as PublicGiftRegistryDto;
    }
  } catch {
    registry = null;
  }

  if (!registry) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-stone-50 px-4 text-center dark:bg-stone-950">
        <div className="mx-auto max-w-md rounded-2xl border bg-card p-8 shadow-sm">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-amber-500/10 text-amber-600">
            <Gift className="h-7 w-7" />
          </div>

          <h2 className="mt-4 text-2xl font-serif font-bold text-foreground">
            Registry Not Available
          </h2>

          <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
            This wedding gift registry is either no longer active or the share link has been rotated or expired.
          </p>

          <p className="mt-2 text-xs text-muted-foreground">
            Please check with the wedding hosts for the most recent link.
          </p>

          <div className="mt-6">
            <Link href="/">
              <Button variant="outline" size="sm">
                Return to UtsavAI
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <PublicRegistryView shareToken={shareToken} initialRegistry={registry} />;
}
