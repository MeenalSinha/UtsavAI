import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { routes } from "@/config/routes";
import { WorkspaceNav } from "@/features/events/components/workspace-nav";
import { GiftWorkspace } from "@/features/gifts/components/gift-workspace";
import { loadOrNavigate } from "@/lib/api/load";
import { serverGet } from "@/lib/api/server";
import type { EventDto } from "@/types/api";

export const metadata: Metadata = { title: "GiftCircle Registry | UtsavAI" };

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default async function EventGiftCirclePage({
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
        <h1 className="text-3xl font-semibold">GiftCircle Registry</h1>
        <p className="text-muted-foreground">
          Curated wedding wishlist, group gifting funds, and guest gift coordination for {event.title}.
        </p>
      </header>

      <WorkspaceNav eventId={event.id} activeModule="giftcircle" />

      <GiftWorkspace eventId={event.id} />
    </div>
  );
}
