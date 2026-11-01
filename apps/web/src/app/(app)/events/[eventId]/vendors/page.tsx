import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { VendorWorkspace } from "@/features/vendors/components/vendor-workspace";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { EventDto } from "@/types/api";

export const metadata: Metadata = { title: "VendorConnect | UtsavAI" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventVendorsPage({
  params,
}: {
  params: Promise<{ eventId: string }>;
}) {
  const { eventId } = await params;
  if (!UUID_RE.test(eventId)) notFound();

  const event = await loadOrNavigate(
    serverGet<EventDto>(`/events/${eventId}`),
    routes.event(eventId),
  );

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold">VendorConnect Management & Comparison</h1>
        <p className="text-muted-foreground">
          Event-scoped vendor directory, commercial quotation tracking, and deterministic side-by-side proposal comparison for {event.title}.
        </p>
      </header>

      <WorkspaceNav eventId={event.id} activeModule="vendorconnect" />

      <VendorWorkspace eventId={event.id} currency={event.currency} />
    </div>
  );
}

